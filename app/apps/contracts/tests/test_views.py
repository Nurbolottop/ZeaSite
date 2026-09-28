from django.contrib.auth.models import User
from django.test import Client

from apps.contracts import services
from apps.contracts.models import Contract, ContractDocument

from .utils import (
    C, DOCX, PDF, PrivateMediaTestCase, Role, S, activate, company_at_contract_stage, draft_contract,
    head, make_company, make_user, pdf, ready_terms, upload,
)

ALL_ROLES = (Role.HEAD, Role.BIZDEV, Role.PM, Role.TECH_LEAD, Role.MARKETING, Role.DEVOPS)


class ContractFixture(PrivateMediaTestCase):
    def setUp(self):
        self.head = head()
        self.bizdev = make_user('biz', Role.BIZDEV)
        self.company = company_at_contract_stage(self.head, name='Kargo Express')
        self.contract = draft_contract(self.company, self.bizdev, number='ZEA-2026-01')
        ready_terms(self.contract, self.bizdev)
        services.upload_contract_file(contract=self.contract, uploaded=pdf('Подписанный.pdf'), user=self.bizdev)
        self.spec = services.add_document(
            document=ContractDocument(contract=self.contract, document_type='spec', title='ТЗ CRM'),
            uploaded=upload('tz.docx', DOCX), user=self.bizdev)
        self.act = services.add_document(
            document=ContractDocument(contract=self.contract, document_type='act', title='Акт сентябрь'),
            uploaded=upload('act.pdf', PDF), user=self.bizdev)
        self.users = {role: make_user(f'user-{i}', role) for i, role in enumerate(ALL_ROLES)}

    def login(self, role):
        self.client.force_login(self.users[role])


class ContractListAndCardTests(ContractFixture):
    def test_list_columns_search_filters(self):
        other = company_at_contract_stage(self.head, name='EduStart')
        draft_contract(other, self.head, number='EDU-7')
        self.login(Role.HEAD)
        resp = self.client.get('/hub/contracts/')
        self.assertContains(resp, 'ZEA-2026-01')
        self.assertContains(resp, '17,5 %')
        self.assertContains(resp, 'Продажи через созданную ZEA систему')

        def numbers(query):
            return {c.number for c in self.client.get('/hub/contracts/' + query).context['contracts']}
        self.assertEqual(numbers('?q=EDU'), {'EDU-7'})
        self.assertEqual(numbers('?q=kargo'), {'ZEA-2026-01'})
        self.assertEqual(numbers(f'?company={other.pk}'), {'EDU-7'})
        self.assertEqual(numbers('?status=draft'), {'ZEA-2026-01', 'EDU-7'})
        self.assertEqual(numbers('?status=active'), set())
        # период: договор с 01.10.2026 бессрочный
        self.assertEqual(numbers('?date_from=2026-11-01&date_to=2026-12-01'), {'ZEA-2026-01'})
        self.assertEqual(numbers('?date_to=2026-09-01'), set())

    def test_card_for_manager(self):
        self.login(Role.BIZDEV)
        resp = self.client.get(f'/hub/contracts/{self.contract.pk}/')
        for text in ('Договор № ZEA-2026-01', '17,5 %', 'Продажи через CRM', 'Подписанный.pdf',
                     'ТЗ CRM', 'Акт сентябрь', 'История статусов', 'Редактировать', 'Изменить статус'):
            self.assertContains(resp, text)

    def test_company_card_contract_block(self):
        self.login(Role.BIZDEV)
        resp = self.client.get(f'/hub/candidates/{self.company.pk}/')
        self.assertContains(resp, 'ZEA-2026-01')
        self.assertContains(resp, 'Черновик')
        self.assertNotContains(resp, 'Оформить как партнёра')
        self.contract.refresh_from_db()
        services.change_contract_status(contract=self.contract, to_status=C.REVIEW, user=self.bizdev)
        services.change_contract_status(contract=self.contract, to_status=C.READY, user=self.bizdev)
        services.change_contract_status(contract=self.contract, to_status=C.ACTIVE, user=self.head)
        resp = self.client.get(f'/hub/candidates/{self.company.pk}/')
        self.assertContains(resp, 'Действует')
        self.assertContains(resp, 'Оформить как партнёра')
        self.assertContains(resp, 'data-confirm="Оформить')

    def test_make_partner_via_card(self):
        self.login(Role.BIZDEV)
        url = f'/hub/candidates/{self.company.pk}/make-partner/'
        resp = self.client.post(url, follow=True)
        self.assertContains(resp, 'только при действующем')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.CONTRACT)
        activate(Contract.objects.get(pk=self.contract.pk), self.head, with_file=False)
        resp = self.client.post(url)
        self.assertRedirects(resp, f'/hub/partners/{self.company.pk}/')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.PARTNER)
        self.assertEqual(self.client.get(url).status_code, 405)  # только POST

    def test_create_and_edit_via_forms(self):
        self.login(Role.BIZDEV)
        company = company_at_contract_stage(self.head, name='Новый партнёр')
        form = self.client.get(f'/hub/contracts/add/?company={company.pk}')
        self.assertEqual(form.context['form'].initial['company'], company.pk)
        resp = self.client.post('/hub/contracts/add/', {
            'company': company.pk, 'number': 'NEW-1', 'title': 'Договор',
            'share_percent': '12.5', 'calculation_base_type': 'other', 'calculation_base_description': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('calculation_base_description', resp.context['form'].errors)
        resp = self.client.post('/hub/contracts/add/', {
            'company': company.pk, 'number': 'NEW-1', 'title': 'Договор',
            'share_percent': '12.5', 'calculation_base_type': 'profit',
        })
        contract = Contract.objects.get(number='NEW-1')
        self.assertRedirects(resp, f'/hub/contracts/{contract.pk}/')
        self.client.post(f'/hub/contracts/{contract.pk}/edit/', {
            'number': 'NEW-1', 'title': 'Договор (ред.)', 'share_percent': '15',
            'calculation_base_type': 'profit', 'company': self.company.pk,  # попытка сменить компанию
        })
        contract.refresh_from_db()
        self.assertEqual((contract.title, str(contract.share_percent), contract.company), ('Договор (ред.)', '15.00', company))

    def test_upload_forms(self):
        self.login(Role.BIZDEV)
        url = f'/hub/contracts/{self.contract.pk}/file/'
        resp = self.client.post(url, {'file': upload('virus.exe', b'MZ')})
        self.assertContains(resp, 'Недопустимый тип файла')
        resp = self.client.post(url, {'file': pdf('новый.pdf')})
        self.assertRedirects(resp, f'/hub/contracts/{self.contract.pk}/')
        resp = self.client.post(f'/hub/contracts/{self.contract.pk}/documents/add/', {
            'document_type': 'supplement', 'title': 'Допсоглашение №1', 'upload': upload('ds.pdf', PDF)})
        self.assertRedirects(resp, f'/hub/contracts/{self.contract.pk}/')
        self.assertTrue(self.contract.documents.filter(title='Допсоглашение №1').exists())


class ContractPermissionTests(ContractFixture):
    def get(self, role, url):
        self.login(role)
        return self.client.get(url).status_code

    def test_matrix(self):
        pk = self.contract.pk
        read = ['/hub/contracts/', f'/hub/contracts/{pk}/']
        manage = ['/hub/contracts/add/', f'/hub/contracts/{pk}/edit/', f'/hub/contracts/{pk}/status/',
                  f'/hub/contracts/{pk}/file/', f'/hub/contracts/{pk}/documents/add/']
        expected = {
            Role.HEAD: (200, 200), Role.BIZDEV: (200, 200),
            Role.PM: (200, 403), Role.TECH_LEAD: (200, 403),
            Role.MARKETING: (403, 403), Role.DEVOPS: (403, 403),
        }
        for role, (read_code, manage_code) in expected.items():
            for url in read:
                self.assertEqual(self.get(role, url), read_code, (role, url))
            for url in manage:
                self.assertEqual(self.get(role, url), manage_code, (role, url))

    def test_menu_visibility(self):
        for role, visible in ((Role.PM, True), (Role.TECH_LEAD, True), (Role.MARKETING, False), (Role.DEVOPS, False)):
            self.login(role)
            modules = {e['item'].module for e in self.client.get('/hub/').context['nav_menu']}
            self.assertEqual('contracts' in modules, visible, role)

    def test_financial_terms_hidden(self):
        for role in (Role.PM, Role.TECH_LEAD):
            self.login(role)
            for url in ('/hub/contracts/', f'/hub/contracts/{self.contract.pk}/',
                        f'/hub/candidates/{self.company.pk}/'):
                html = self.client.get(url).content.decode()
                for secret in ('17,5', 'Продажи через CRM', 'Продажи через созданную ZEA систему',
                               'Подписанный.pdf', 'Акт сентябрь'):
                    self.assertNotIn(secret, html, (role, url, secret))
            card = self.client.get(f'/hub/contracts/{self.contract.pk}/')
            self.assertContains(card, 'ТЗ CRM')  # ТЗ видно
            self.assertContains(card, 'скрыто')

    def test_marketing_sees_company_but_not_contracts(self):
        self.login(Role.MARKETING)
        resp = self.client.get(f'/hub/candidates/{self.company.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'ZEA-2026-01')

    def test_downloads(self):
        file_url = f'/hub/contracts/{self.contract.pk}/file/download/'
        spec_url = f'/hub/contracts/documents/{self.spec.uid}/download/'
        act_url = f'/hub/contracts/documents/{self.act.uid}/download/'
        expected = {
            Role.HEAD: (200, 200, 200), Role.BIZDEV: (200, 200, 200),
            Role.PM: (403, 200, 403), Role.TECH_LEAD: (403, 200, 403),
            Role.MARKETING: (403, 403, 403), Role.DEVOPS: (403, 403, 403),
        }
        for role, codes in expected.items():
            self.assertEqual(tuple(self.get(role, u) for u in (file_url, spec_url, act_url)), codes, role)

    def test_download_response_is_safe_attachment(self):
        self.login(Role.HEAD)
        resp = self.client.get(f'/hub/contracts/{self.contract.pk}/file/download/')
        self.assertEqual(b''.join(resp.streaming_content), PDF)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp['Content-Disposition'].startswith('attachment'))
        self.assertIn("sandbox", resp['Content-Security-Policy'])
        self.assertEqual(resp['X-Content-Type-Options'], 'nosniff')
        self.assertIn('no-store', resp['Cache-Control'])

    def test_no_direct_or_guessable_urls(self):
        self.login(Role.HEAD)
        name = self.contract.file.name
        for url in (f'/media/{name}', f'/private_media/{name}', f'/hub/private_media/{name}'):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        # документы — только по UUID; числовой id не работает, чужой UUID — 404
        self.assertEqual(self.client.get(f'/hub/contracts/documents/{self.spec.pk}/download/').status_code, 404)
        self.assertEqual(self.client.get(
            '/hub/contracts/documents/00000000-0000-0000-0000-000000000000/download/').status_code, 404)
        self.client.logout()
        resp = self.client.get(f'/hub/contracts/documents/{self.spec.uid}/download/')
        self.assertTrue(resp['Location'].startswith('/hub/login/'))

    def test_direct_posts_without_rights(self):
        pk = self.contract.pk
        services.change_contract_status(contract=self.contract, to_status=C.REVIEW, user=self.bizdev)
        services.change_contract_status(contract=self.contract, to_status=C.READY, user=self.bizdev)
        # Менеджер по развитию: активация прямым POST — 403
        self.login(Role.BIZDEV)
        self.assertEqual(self.client.post(f'/hub/contracts/{pk}/status/', {'to_status': 'active'}).status_code, 403)
        # PM: любые изменения — 403
        self.login(Role.PM)
        for url, data in ((f'/hub/contracts/{pk}/status/', {'to_status': 'active'}),
                          (f'/hub/contracts/{pk}/edit/', {'number': 'X', 'title': 'X', 'share_percent': '90'}),
                          (f'/hub/contracts/{pk}/file/', {'file': pdf()}),
                          (f'/hub/contracts/{pk}/documents/add/', {'document_type': 'spec', 'title': 'x', 'upload': pdf()}),
                          ('/hub/contracts/add/', {'company': self.company.pk, 'number': 'Y', 'title': 'Y'})):
            self.assertEqual(self.client.post(url, data).status_code, 403, url)
        self.contract.refresh_from_db()
        self.assertEqual((self.contract.status, str(self.contract.share_percent)), (C.READY, '17.50'))
        self.assertEqual(self.contract.documents.count(), 2)
        # Руководитель активирует
        self.login(Role.HEAD)
        self.client.post(f'/hub/contracts/{pk}/status/', {'to_status': 'active'})
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, C.ACTIVE)
        # после подписания процент не меняется даже Руководителем
        self.client.post(f'/hub/contracts/{pk}/edit/', {'number': 'ZEA-2026-01', 'title': 'x', 'share_percent': '90',
                                                         'calculation_base_type': 'profit'})
        self.contract.refresh_from_db()
        self.assertEqual(str(self.contract.share_percent), '17.50')

    def test_csrf_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.users[Role.HEAD])
        resp = client.post(f'/hub/contracts/{self.contract.pk}/status/', {'to_status': 'review'})
        self.assertEqual(resp.status_code, 403)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, C.DRAFT)

    def test_superuser(self):
        self.client.force_login(User.objects.create_superuser('root', password='x'))
        for url in ('/hub/contracts/', f'/hub/contracts/{self.contract.pk}/', '/hub/contracts/add/',
                    f'/hub/contracts/{self.contract.pk}/file/download/',
                    f'/hub/contracts/documents/{self.act.uid}/download/',
                    f'/admin/contracts/contract/{self.contract.pk}/change/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_dashboard_contract_counts(self):
        services.change_contract_status(contract=self.contract, to_status=C.REVIEW, user=self.bizdev)
        self.login(Role.HEAD)
        stats = self.client.get('/hub/').context['contract_stats']
        self.assertEqual((stats['review'], stats['ready'], stats['active']), (1, 0, 0))
        self.login(Role.MARKETING)
        self.assertNotIn('contract_stats', self.client.get('/hub/').context)
