"""Форма заявки: тип обращения, направление, компания/сфера — пока внутри message."""
from django.test import TestCase
from django.utils import translation

from apps.contacts.choices import REQUEST_TYPE_CHOICES, SERVICE_CHOICES
from apps.contacts.forms import ContactForm
from apps.contacts.models import ContactMessage


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
