from django.test import TestCase

from apps.partners import services
from apps.partners.models import CandidateAssessment, Company, CompanyContact
from apps.users.roles import Role

from .utils import S, head, make_company, make_user, move_to


class CandidateListTests(TestCase):
    def setUp(self):
        self.head = head()
        self.bizdev = make_user('biz', Role.BIZDEV, first_name='Бекзат')
        self.client.force_login(self.head)
        self.alpha = make_company(self.head, name='Альфа Маркет', manager=self.bizdev, industry='Ритейл')
        self.beta = make_company(self.head, name='Бета Стартап', company_type='startup')
        self.gamma = move_to(make_company(self.head, name='Гамма Логистик'), S.ANALYSIS, self.head)
        self.partner = move_to(make_company(self.head, name='Дельта Партнёр'), S.PARTNER, self.head)
        self.rejected = make_company(self.head, name='Отказ Групп')
        services.change_status(company=self.rejected, to_status=S.REJECTED, user=self.head, comment='Нет')

    def names(self, url):
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        return {c.name for c in resp.context['companies']}

    def test_default_list_is_active_pipeline(self):
        self.assertEqual(self.names('/hub/candidates/'), {'Альфа Маркет', 'Бета Стартап', 'Гамма Логистик'})

    def test_partner_never_in_candidates(self):
        self.assertNotIn('Дельта Партнёр', self.names('/hub/candidates/?status=all'))
        # «partner» нет среди значений фильтра → фильтр игнорируется, партнёр не появляется
        self.assertEqual(self.names('/hub/candidates/?status=partner'),
                         {'Альфа Маркет', 'Бета Стартап', 'Гамма Логистик'})

    def test_rejected_visible_by_filter(self):
        self.assertEqual(self.names('/hub/candidates/?status=rejected'), {'Отказ Групп'})
        self.assertIn('Отказ Групп', self.names('/hub/candidates/?status=all'))

    def test_search(self):
        self.assertEqual(self.names('/hub/candidates/?q=бета'), {'Бета Стартап'})
        self.assertEqual(self.names('/hub/candidates/?q=несуществующая'), set())

    def test_filters(self):
        self.assertEqual(self.names('/hub/candidates/?status=analysis'), {'Гамма Логистик'})
        self.assertEqual(self.names('/hub/candidates/?type=startup'), {'Бета Стартап'})
        self.assertEqual(self.names(f'/hub/candidates/?manager={self.bizdev.pk}'), {'Альфа Маркет'})
        self.assertEqual(self.names('/hub/candidates/?manager=none'), {'Бета Стартап', 'Гамма Логистик'})

    def test_sorting(self):
        resp = self.client.get('/hub/candidates/?sort=name')
        self.assertEqual([c.name for c in resp.context['companies']],
                         ['Альфа Маркет', 'Бета Стартап', 'Гамма Логистик'])
        resp = self.client.get('/hub/candidates/?sort=-status')
        self.assertEqual(resp.context['companies'][0].name, 'Гамма Логистик')

    def test_pagination(self):
        for i in range(25):
            make_company(self.head, name=f'Компания {i:02d}')
        first = self.client.get('/hub/candidates/?sort=name')
        self.assertEqual(len(first.context['companies']), 20)
        self.assertTrue(first.context['is_paginated'])
        second = self.client.get('/hub/candidates/?sort=name&page=2')
        self.assertEqual(len(second.context['companies']), 8)
        self.assertContains(first, '?sort=name&page=2')

    def test_partners_section(self):
        self.assertEqual(self.names('/hub/partners/'), {'Дельта Партнёр'})
        self.assertEqual(self.names('/hub/partners/?q=дельта'), {'Дельта Партнёр'})
        self.assertEqual(self.names('/hub/partners/?type=startup'), set())
        resp = self.client.get('/hub/partners/')
        self.assertContains(resp, f'/hub/partners/{self.partner.pk}/')
        self.assertNotContains(resp, 'Добавить кандидата')

    def test_list_shows_columns(self):
        resp = self.client.get('/hub/candidates/')
        self.assertContains(resp, 'Бекзат')
        self.assertContains(resp, 'Ритейл')
        self.assertContains(resp, 'zh-status-analysis')
        self.assertContains(resp, 'Добавить кандидата')


class CompanyCardTests(TestCase):
    def setUp(self):
        self.head = head()
        self.bizdev = make_user('biz', Role.BIZDEV, first_name='Бекзат')
        self.client.force_login(self.bizdev)

    def test_create_candidate(self):
        resp = self.client.post('/hub/candidates/add/', {
            'name': 'Новая Компания', 'company_type': 'startup', 'industry': 'EdTech',
            'website': 'https://example.kg', 'source': 'referral', 'manager': self.bizdev.pk,
        })
        company = Company.objects.get(name='Новая Компания')
        self.assertRedirects(resp, f'/hub/candidates/{company.pk}/')
        self.assertEqual((company.status, company.created_by, company.manager),
                         (S.NEW, self.bizdev, self.bizdev))
        self.assertEqual(company.status_history.count(), 1)

    def test_create_form_defaults_manager_and_validates(self):
        resp = self.client.get('/hub/candidates/add/')
        self.assertEqual(resp.context['form'].initial.get('manager'), self.bizdev.pk)
        resp = self.client.post('/hub/candidates/add/', {'name': '', 'company_type': 'business'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].errors['name'])
        self.assertFalse(Company.objects.exists())

    def test_status_cannot_be_set_via_edit_form(self):
        company = make_company(self.head)
        self.client.post(f'/hub/candidates/{company.pk}/edit/', {
            'name': 'Переименована', 'company_type': 'business', 'status': S.PARTNER,
        })
        company.refresh_from_db()
        self.assertEqual((company.name, company.status), ('Переименована', S.NEW))
        self.assertEqual(company.updated_by, self.bizdev)

    def test_detail_card(self):
        company = move_to(make_company(self.head, manager=self.bizdev, notes='Звонить после 15:00'),
                          S.ANALYSIS, self.head)
        services.save_contact(contact=CompanyContact(company=company, name='Айгуль', position='CEO',
                                                     is_primary=True))
        resp = self.client.get(f'/hub/candidates/{company.pk}/')
        for text in ('Альфа', 'Айгуль', 'CEO', 'основной', 'Звонить после 15:00', 'История статусов',
                     'Анализ ещё не заполнен', 'Заполнить анализ', 'Изменить статус'):
            self.assertContains(resp, text)
        self.assertNotContains(resp, 'Решение команды')  # менеджер не принимает решения

    def test_contact_crud(self):
        company = make_company(self.head)
        resp = self.client.post(f'/hub/candidates/{company.pk}/contacts/add/', {
            'name': 'Азамат', 'telegram': '@azamat', 'is_primary': 'on',
        })
        self.assertRedirects(resp, f'/hub/candidates/{company.pk}/')
        contact = company.contacts.get()
        self.client.post(f'/hub/candidates/{company.pk}/contacts/{contact.pk}/edit/',
                         {'name': 'Азамат Н.', 'position': 'CTO'})
        contact.refresh_from_db()
        self.assertEqual((contact.name, contact.position, contact.is_primary), ('Азамат Н.', 'CTO', False))
        # чужой контакт через URL другой компании недоступен
        other = make_company(self.head, name='Другая')
        self.assertEqual(self.client.get(f'/hub/candidates/{other.pk}/contacts/{contact.pk}/edit/').status_code, 404)
        self.assertContains(self.client.get(f'/hub/candidates/{company.pk}/contacts/{contact.pk}/delete/'),
                            'Удалить контакт?')
        self.client.post(f'/hub/candidates/{company.pk}/contacts/{contact.pk}/delete/')
        self.assertFalse(CompanyContact.objects.exists())
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())

    def test_assessment_via_card(self):
        company = make_company(self.head)
        resp = self.client.post(f'/hub/candidates/{company.pk}/assessment/', {
            'business_model': 'Подписка', 'mvp_state': 'in_progress', 'revenue': 'не раскрыта',
        })
        self.assertRedirects(resp, f'/hub/candidates/{company.pk}/')
        self.assertEqual(company.assessment.business_model, 'Подписка')
        self.client.post(f'/hub/candidates/{company.pk}/assessment/', {'business_model': 'Маркетплейс'})
        self.assertEqual(CandidateAssessment.objects.get().business_model, 'Маркетплейс')
        self.assertContains(self.client.get(f'/hub/candidates/{company.pk}/'), 'Маркетплейс')

    def test_status_change_via_card(self):
        company = make_company(self.head)
        resp = self.client.get(f'/hub/candidates/{company.pk}/status/')
        self.assertEqual([c[0] for c in resp.context['form'].fields['to_status'].choices],
                         [S.ANALYSIS, S.REJECTED])
        self.assertContains(resp, 'data-confirm-when="to_status=rejected"')
        self.client.post(f'/hub/candidates/{company.pk}/status/', {'to_status': S.ANALYSIS, 'comment': 'Старт'})
        company.refresh_from_db()
        self.assertEqual(company.status, S.ANALYSIS)

    def test_reject_via_card_requires_reason(self):
        company = make_company(self.head)
        resp = self.client.post(f'/hub/candidates/{company.pk}/status/', {'to_status': S.REJECTED})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Укажите причину отклонения')
        company.refresh_from_db()
        self.assertEqual(company.status, S.NEW)

    def test_invalid_transition_via_card(self):
        company = make_company(self.head)
        resp = self.client.post(f'/hub/candidates/{company.pk}/status/', {'to_status': S.PARTNER})
        self.assertEqual(resp.status_code, 200)
        company.refresh_from_db()
        self.assertEqual(company.status, S.NEW)

    def test_decision_via_card(self):
        self.client.force_login(self.head)
        company = move_to(make_company(self.head), S.DISCUSSION, self.head)
        resp = self.client.post(f'/hub/candidates/{company.pk}/decision/', {
            'review_date': '2026-09-28', 'decision': 'approve', 'comment': 'Единогласно',
        })
        self.assertRedirects(resp, f'/hub/candidates/{company.pk}/')
        company.refresh_from_db()
        self.assertEqual(company.status, S.APPROVED)
        card = self.client.get(f'/hub/candidates/{company.pk}/')
        self.assertContains(card, 'Единогласно')
        self.assertContains(card, '28.09.2026')

    def test_partner_card_lives_in_partners_section(self):
        company = move_to(make_company(self.head), S.PARTNER, self.head)
        self.assertRedirects(self.client.get(f'/hub/candidates/{company.pk}/'), f'/hub/partners/{company.pk}/')
        resp = self.client.get(f'/hub/partners/{company.pk}/')
        self.assertContains(resp, 'Партнёр ZEA')
        active = [e['item'].module for e in resp.context['nav_menu'] if e['active']]
        self.assertEqual(active, ['partners'])
        # кандидат по URL партнёров → в раздел кандидатов
        candidate = make_company(self.head, name='Кандидат')
        self.assertRedirects(self.client.get(f'/hub/partners/{candidate.pk}/'), f'/hub/candidates/{candidate.pk}/')

    def test_unknown_company_404(self):
        self.assertEqual(self.client.get('/hub/candidates/999/').status_code, 404)
