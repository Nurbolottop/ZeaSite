from django.contrib.auth.models import User
from django.test import TestCase

from apps.partners.models import Company
from apps.users.roles import Role

from .utils import S, head, make_company, make_user, move_to

VIEW_ONLY = (Role.PM, Role.TECH_LEAD, Role.MARKETING)


class PermissionMatrixTests(TestCase):
    def setUp(self):
        self.owner = head('owner')
        self.company = move_to(make_company(self.owner), S.DISCUSSION, self.owner)
        self.partner = move_to(make_company(self.owner, name='Партнёр'), S.PARTNER, self.owner)
        pk = self.company.pk
        self.read_urls = ['/hub/candidates/', f'/hub/candidates/{pk}/', '/hub/partners/',
                          f'/hub/partners/{self.partner.pk}/']
        self.edit_urls = ['/hub/candidates/add/', f'/hub/candidates/{pk}/edit/',
                          f'/hub/candidates/{pk}/status/', f'/hub/candidates/{pk}/assessment/',
                          f'/hub/candidates/{pk}/contacts/add/']
        self.decide_url = f'/hub/candidates/{pk}/decision/'

    def codes(self, user, urls):
        self.client.force_login(user)
        return {url: self.client.get(url, follow=False).status_code for url in urls}

    def assertAll(self, codes, expected):
        self.assertEqual(set(codes.values()), {expected}, codes)

    def test_head_full_access(self):
        user = make_user('h', Role.HEAD)
        self.assertAll(self.codes(user, self.read_urls[:3] + self.edit_urls + [self.decide_url]), 200)

    def test_bizdev_edits_but_does_not_decide(self):
        user = make_user('b', Role.BIZDEV)
        self.assertAll(self.codes(user, self.read_urls[:3] + self.edit_urls), 200)
        self.assertEqual(self.codes(user, [self.decide_url])[self.decide_url], 403)

    def test_view_only_roles(self):
        for role in VIEW_ONLY:
            user = make_user(f'u-{role}', role)
            self.assertAll(self.codes(user, self.read_urls[:3]), 200)
            self.assertAll(self.codes(user, self.edit_urls + [self.decide_url]), 403)
            card = self.client.get(f'/hub/candidates/{self.company.pk}/')
            for button in ('Редактировать', 'Изменить статус', 'Заполнить анализ', 'Решение команды'):
                self.assertNotContains(card, button)
            self.assertNotContains(self.client.get('/hub/candidates/'), 'Добавить кандидата')

    def test_view_only_roles_cannot_post(self):
        user = make_user('pm', Role.PM)
        self.client.force_login(user)
        pk = self.company.pk
        self.assertEqual(self.client.post('/hub/candidates/add/', {'name': 'Взлом'}).status_code, 403)
        self.assertEqual(self.client.post(f'/hub/candidates/{pk}/status/',
                                          {'to_status': S.REJECTED, 'comment': 'x'}).status_code, 403)
        self.assertEqual(self.client.post(self.decide_url, {'decision': 'approve'}).status_code, 403)
        self.assertFalse(Company.objects.filter(name='Взлом').exists())
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.DISCUSSION)

    def test_devops_has_no_access(self):
        user = make_user('ops', Role.DEVOPS)
        self.assertAll(self.codes(user, self.read_urls + self.edit_urls + [self.decide_url]), 403)
        # 403, а не 404, даже для несуществующей компании — id не раскрываются
        self.assertEqual(self.client.get('/hub/candidates/9999/edit/').status_code, 403)
        dashboard = self.client.get('/hub/')
        self.assertNotContains(dashboard, '/hub/candidates/')
        self.assertNotContains(dashboard, 'Всего кандидатов')

    def test_user_without_role(self):
        self.assertAll(self.codes(make_user('nobody'), self.read_urls), 403)

    def test_superuser_full_access(self):
        root = User.objects.create_superuser('root', password='x')
        self.assertAll(self.codes(root, self.read_urls[:3] + self.edit_urls + [self.decide_url]), 200)

    def test_anonymous_redirected(self):
        for url in self.read_urls + self.edit_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302)
            self.assertTrue(resp['Location'].startswith('/hub/login/'))

    def test_admin_status_readonly(self):
        self.client.force_login(User.objects.create_superuser('root', password='x'))
        resp = self.client.get(f'/admin/partners/company/{self.company.pk}/change/')
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'name="status"')


class DashboardTests(TestCase):
    def test_dashboard_counts(self):
        user = head()
        make_company(user, name='A')
        move_to(make_company(user, name='B'), S.ANALYSIS, user)
        move_to(make_company(user, name='C'), S.NEGOTIATION, user)
        move_to(make_company(user, name='D'), S.PARTNER, user)
        move_to(make_company(user, name='E'), S.PARTNER, user)
        from apps.partners import services
        services.change_status(company=make_company(user, name='F'), to_status=S.REJECTED,
                               user=user, comment='нет')
        self.client.force_login(make_user('pm', Role.PM))
        stats = self.client.get('/hub/').context['partner_stats']
        self.assertEqual((stats['candidates_total'], stats['analysis'], stats['negotiation'],
                          stats['partners'], stats['rejected']), (3, 1, 1, 2, 1))
        by_status = {step['value']: step['count'] for step in stats['pipeline']}
        self.assertEqual(by_status[S.NEW], 1)

    def test_dashboard_renders_empty(self):
        self.client.force_login(head())
        resp = self.client.get('/hub/')
        self.assertContains(resp, 'Всего кандидатов')
        self.assertContains(resp, 'Кандидаты по стадиям')
