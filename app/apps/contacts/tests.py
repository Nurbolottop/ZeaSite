"""Форма заявки: тип обращения, направление, компания/сфера — пока внутри message."""
from django.test import TestCase
from django.utils import translation

from apps.contacts.choices import REQUEST_TYPE_CHOICES, SERVICE_CHOICES
from apps.contacts.forms import ContactForm
from apps.contacts.models import ContactMessage
from apps.contacts.models import Brief


class ContactFormTests(TestCase):
    def post(self, **data):
        base = {'name': 'Айбек', 'phone': '+996 555 000 000', 'message': 'Хотим CRM'}
        base.update(data)
        return self.client.post('/contact/submit/', base)

    def test_partnership_with_company_and_industry(self):
        resp = self.post(request_type='partnership', service='crm', company='ОсОО Тест',
                         industry='Логистика')
        self.assertEqual(resp.json(), {'ok': True})
        msg = ContactMessage.objects.get().message
        self.assertTrue(msg.startswith('[Хочу обсудить партнёрство] [CRM и внутренние системы]'))
        self.assertIn('Компания: ОсОО Тест', msg)
        self.assertIn('Сфера: Логистика', msg)
        self.assertTrue(msg.endswith('Хотим CRM'))

    def test_development_request(self):
        self.post(request_type='development')
        self.assertTrue(ContactMessage.objects.get().message.startswith('[Нужна разработка]\n\n'))

    def test_missing_type_saved_as_other(self):
        self.post()
        self.assertTrue(ContactMessage.objects.get().message.startswith('[Другой вопрос]'))

    def test_tags_are_russian_from_any_language(self):
        with translation.override('en'):
            form = ContactForm({'name': 'A', 'email': 'a@b.co', 'message': 'hi',
                                'request_type': 'development', 'service': 'mobile'})
            self.assertTrue(form.is_valid(), form.errors)
            form.save()
        self.assertTrue(ContactMessage.objects.get().message.startswith(
            '[Нужна разработка] [Мобильное приложение]'))

    def test_invalid_choice_rejected(self):
        resp = self.post(request_type='investment')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('request_type', resp.json()['errors'])
        self.assertFalse(ContactMessage.objects.exists())

    def test_model_unchanged(self):
        """Этап A: без новых полей в ContactMessage."""
        fields = {f.name for f in ContactMessage._meta.get_fields()}
        self.assertEqual(fields, {'id', 'name', 'email', 'phone', 'message', 'source', 'created_at', 'is_read'})

    def test_choices_rendered_from_python(self):
        html = self.client.get('/').content.decode()
        for value, _label in REQUEST_TYPE_CHOICES:
            self.assertIn(f'name="request_type" value="{value}"', html)
        for value, _label in SERVICE_CHOICES:
            self.assertIn(f'<option value="{value}">', html)


class BriefTests(TestCase):
    def payload(self, **extra):
        data = {'name': 'Айбек', 'company': 'Тест ООО', 'phone': '+996700000001',
                'product_types': ['crm', 'mobile'], 'stage': 'idea',
                'idea': 'CRM для сервиса доставки', 'features': 'Заявки, курьеры, отчёты',
                'deadline': '1_3', 'budget': 'discuss', 'consent': 'on'}
        data.update(extra)
        return data

    def test_page_opens_in_all_languages(self):
        for url in ('/brief/', '/ky/brief/', '/en/brief/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            self.assertContains(resp, 'id="brief-form"')
        translation.activate('ru')

    def test_submit_saves_readable_brief(self):
        resp = self.client.post('/brief/', self.payload(), HTTP_X_REQUESTED_WITH='fetch')
        self.assertEqual(resp.json(), {'ok': True})
        brief = Brief.objects.get()
        self.assertEqual((brief.name, brief.company, brief.status), ('Айбек', 'Тест ООО', 'new'))
        self.assertEqual(brief.product_types, 'CRM или внутренняя система, Мобильное приложение')
        self.assertEqual(brief.deadline, 'Через 1–3 месяца')
        steps = {s['step']: {i['label']: i['value'] for i in s['items']} for s in brief.answers}
        self.assertEqual(steps['Продукт']['На каком этапе проект'], 'Есть только идея')
        self.assertNotIn('consent', str(brief.answers))

    def test_kyrgyz_brief_stored_in_russian(self):
        self.client.post('/ky/brief/', self.payload(), HTTP_X_REQUESTED_WITH='fetch')
        translation.activate('ru')
        brief = Brief.objects.get()
        self.assertEqual(brief.language, 'ky')
        self.assertEqual(brief.answers[1]['step'], 'Продукт')

    def test_validation(self):
        resp = self.client.post('/brief/', self.payload(idea='', phone=''), HTTP_X_REQUESTED_WITH='fetch')
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()['errors']
        self.assertIn('idea', errors)
        self.assertIn('__all__', errors)          # нет ни телефона, ни email, ни Telegram
        self.assertFalse(Brief.objects.exists())
        resp = self.client.post('/brief/', self.payload(consent=''), HTTP_X_REQUESTED_WITH='fetch')
        self.assertIn('consent', resp.json()['errors'])

    def test_honeypot_blocks_bots(self):
        resp = self.client.post('/brief/', self.payload(website='http://spam'), HTTP_X_REQUESTED_WITH='fetch')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Brief.objects.exists())

    def test_no_js_submit_shows_thanks(self):
        resp = self.client.post('/brief/', self.payload())
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'id="brief-form"')
        self.assertEqual(Brief.objects.count(), 1)

    def test_links_on_home(self):
        self.assertContains(self.client.get('/'), 'href="/brief/"')
