"""Смоук-тесты публичного сайта zeastudio.su: он должен работать без авторизации
и не зависеть от ZEA Hub."""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from apps.contacts.models import ContactMessage


class PublicSiteTests(TestCase):
    def test_home_pages_open_without_auth(self):
        for url in ('/', '/ky/', '/en/'):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            self.assertContains(resp, 'id="contact-form"')

    def test_seo_endpoints(self):
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
        robots = self.client.get('/robots.txt')
        self.assertEqual(robots.status_code, 200)
        self.assertContains(robots, 'Disallow: /hub/')

    def test_language_switch(self):
        resp = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        self.assertEqual(resp.status_code, 302)

    def test_contact_form_submit(self):
        resp = self.client.post('/contact/submit/', {
            'name': 'Клиент', 'phone': '+996 555 111 222', 'message': 'Нужен сайт', 'service': 'website',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {'ok': True})
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.source, 'form')
        self.assertIn('Нужен сайт', msg.message)

    def test_contact_form_validation(self):
        resp = self.client.post('/contact/submit/', {'name': 'Без контактов', 'message': 'x'})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])
        self.assertFalse(ContactMessage.objects.exists())

    def test_contact_form_requires_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        resp = csrf_client.post('/contact/submit/', {'name': 'x', 'phone': '1', 'message': 'x'})
        self.assertEqual(resp.status_code, 403)

    def test_site_works_for_logged_in_hub_user(self):
        self.client.force_login(User.objects.create_user('staff', password='x'))
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_hub_assets_not_loaded_on_site(self):
        html = self.client.get('/').content.decode()
        self.assertNotIn('hub/hub.css', html)
        self.assertNotIn('bootstrap@', html)
