from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from apps.users.roles import Role

from .navigation import NAVIGATION


class HubAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pm', password='secret-pass-123', first_name='Анна')
        self.user.groups.add(Group.objects.get(name=Role.PM))

    def test_urls_live_under_hub(self):
        self.assertEqual(reverse('hub:dashboard'), '/hub/')
        self.assertEqual(reverse('hub:login'), '/hub/login/')
        self.assertEqual(reverse('hub:logout'), '/hub/logout/')
        for item in NAVIGATION:
            self.assertTrue(reverse(item.url_name).startswith('/hub/'), item.url_name)

    def test_anonymous_redirected_to_hub_login(self):
        for url in ('/hub/', '/hub/candidates/', '/hub/finance/'):
            resp = self.client.get(url)
            self.assertRedirects(resp, f'/hub/login/?next={url}', fetch_redirect_response=False)

    def test_unknown_hub_url_does_not_leak(self):
        # несуществующий URL под /hub/ — 404, без данных
        self.assertEqual(self.client.get('/hub/unknown/').status_code, 404)

    def test_login_redirects_to_hub(self):
        resp = self.client.post('/hub/login/', {'username': 'pm', 'password': 'secret-pass-123'})
        self.assertRedirects(resp, '/hub/')
        resp = self.client.get('/hub/')
        self.assertContains(resp, 'Анна')
        self.assertContains(resp, Role.PM)

    def test_login_respects_next(self):
        resp = self.client.post('/hub/login/?next=/hub/projects/',
                                {'username': 'pm', 'password': 'secret-pass-123', 'next': '/hub/projects/'})
        self.assertRedirects(resp, '/hub/projects/')

    def test_wrong_password(self):
        resp = self.client.post('/hub/login/', {'username': 'pm', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'alert-danger')

    def test_hub_is_russian_even_if_site_language_is_english(self):
        self.client.cookies['django_language'] = 'en'
        resp = self.client.post('/hub/login/', {'username': 'pm', 'password': 'wrong'},
                                HTTP_ACCEPT_LANGUAGE='en')
        self.assertContains(resp, 'Пожалуйста, введите правильные')

    def test_logout(self):
        self.client.force_login(self.user)
        resp = self.client.post('/hub/logout/')
        self.assertRedirects(resp, '/hub/login/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/hub/').status_code, 302)

    def test_logged_in_user_skips_login_page(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get('/hub/login/'), '/hub/')

    def test_hub_pages_isolated_from_site_assets(self):
        self.client.force_login(self.user)
        html = self.client.get('/hub/').content.decode()
        self.assertIn('hub/hub.css', html)
        for site_asset in ('tailwind', 'aos.css', 'lucide'):
            self.assertNotIn(site_asset, html)

    def test_role_user_sees_placeholders(self):
        self.client.force_login(self.user)
        resp = self.client.get('/hub/candidates/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'в разработке')

    def test_user_without_role_gets_hub_403(self):
        self.client.force_login(User.objects.create_user('nobody', password='x'))
        self.assertEqual(self.client.get('/hub/').status_code, 200)
        resp = self.client.get('/hub/finance/')
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'нет доступа', status_code=403)
        self.assertContains(resp, 'hub-sidebar', status_code=403)
        self.assertNotContains(self.client.get('/hub/'), '/hub/finance/')

    def test_superuser_without_groups_has_full_access(self):
        self.client.force_login(User.objects.create_superuser('root', password='x'))
        for item in NAVIGATION:
            self.assertEqual(self.client.get(reverse(item.url_name)).status_code, 200, item.module)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get('/admin/auth/user/').status_code, 200)
