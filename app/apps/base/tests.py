"""Смоук-тесты публичного сайта zeastudio.su: он должен работать без авторизации
и не зависеть от ZEA Hub."""
import json
import re
import tempfile

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings

from apps.base import views as site_views
from apps.cms.models import Partner, Project, SiteSettings, Stat, TeamMember
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


class PositioningTests(TestCase):
    def html(self, url='/'):
        return self.client.get(url).content.decode()

    def test_hero_uses_cms_title_and_ctas(self):
        html = self.html()
        self.assertIn('технологический партнёр для бизнеса', html)
        self.assertRegex(html, r'href="#contact" data-request-type="partnership"')
        self.assertRegex(html, r'href="#contact" data-request-type="development"')
        s = SiteSettings.get()
        s.hero_title = s.hero_title_ru = 'Проверка — заголовка из CMS'
        s.save()
        self.assertIn('Проверка —', self.html())

    def test_old_positioning_removed(self):
        html = self.html()
        for phrase in ('мини IT-студия', 'UI/UX мирового уровня', 'цифровое будущее',
                       'KIKI Academy', 'разработка цифровых решений', 'Бишкек'):
            self.assertNotIn(phrase, html, phrase)

    def test_new_blocks_rendered(self):
        html = self.html()
        for text in ('Технологическое партнёрство', 'Разработка под заказ', 'Основной формат',
                     'Условия и договор', 'Что мы берём на себя', 'Проектирование',
                     'Мобильные приложения', 'Интеграции', 'Прозрачные условия',
                     'Сначала задача бизнеса — потом технология.'):
            self.assertIn(text, html, text)

    def test_translations(self):
        en, ky = self.html('/en/'), self.html('/ky/')
        self.assertIn('a technology partner for business</span>', en)
        self.assertIn('Technology partnership', en)
        self.assertIn('to work together', en)
        self.assertIn('Discuss a partnership', en)
        self.assertIn('бизнес үчүн технологиялык өнөктөш', ky)
        self.assertIn('Технологиялык өнөктөштүк', ky)
        self.assertIn('Кайрылуунун түрү', ky)


class OptionalSectionsTests(TestCase):
    def html(self):
        return self.client.get('/').content.decode()

    def test_empty_sections_hidden(self):
        html = self.html()
        self.assertNotIn('id="projects"', html)
        self.assertNotIn('href="#projects"', html)
        self.assertNotIn('id="results"', html)
        self.assertNotIn('id="project-modal"', html)
        self.assertNotIn('не добавлены', html)

    def test_projects_and_details(self):
        Project.objects.create(name='Кейс А', description='Описание', project_type='CRM',
                               technologies='Django', task='Задача А', solution='Решение А',
                               result='Итог А', is_featured=True)
        Project.objects.create(name='Скрытый', description='d', project_type='x', technologies='',
                               is_active=False)
        html = self.html()
        self.assertIn('id="projects"', html)
        self.assertIn('href="#projects"', html)
        self.assertIn('id="project-modal"', html)
        pk = Project.objects.get(name='Кейс А').pk
        self.assertIn(f'<template id="project-detail-{pk}">', html)
        self.assertEqual(html.count(f'data-project-open="{pk}"'), 2)  # карточка + hero
        for text in ('Задача А', 'Решение А', 'Итог А'):
            self.assertIn(text, html)
        self.assertNotIn('Скрытый', html)

    def test_stats_grid_and_is_active(self):
        Stat.objects.create(value_text='7', label='лет', icon='rocket', is_counter=True, counter_target=7)
        Stat.objects.create(value_text='9', label='скрытая', is_active=False)
        html = self.html()
        self.assertIn('id="results"', html)
        self.assertIn('data-target="7">7<', html)
        self.assertNotIn('скрытая', html)
        self.assertNotIn('lg:col-span-4', html)

    def test_partners(self):
        Partner.objects.create(name='Партнёр Б', industry='Ритейл')
        html = self.html()
        self.assertIn('id="partners"', html)
        self.assertIn('Партнёр Б', html)


class RedesignSectionsTests(TestCase):
    def html(self):
        return self.client.get('/').content.decode()

    def test_service_illustrations_rendered(self):
        html = self.html()
        # Каждая услуга получает свою SVG-сцену; общие градиенты подключены один раз
        self.assertEqual(html.count('id="z-sLime"'), 1)
        self.assertIn('id="z-auto-t1"', html)   # автоматизация
        self.assertIn('AI и ассистенты', html)
        self.assertNotIn('aos.js', html)
        self.assertNotIn('aos.css', html)
        self.assertNotIn('lucide@latest', html)

    def test_team_hidden_until_filled(self):
        self.assertNotIn('id="team"', self.html())
        TeamMember.objects.create(name='Айбек', role='Разработчик')
        TeamMember.objects.create(name='Скрытый Человек', is_active=False)
        html = self.html()
        self.assertIn('id="team"', html)
        self.assertIn('Айбек', html)
        self.assertNotIn('Скрытый Человек', html)

    def test_about_shows_illustration_without_photo(self):
        self.assertIn('ВАШ ПРОЕКТ', self.html())

    def test_three_formats_get_distinct_illustrations(self):
        from apps.cms.models import CooperationFormat
        CooperationFormat.objects.create(title='Доля', description='d', cta_label='Ок', icon='trending-up',
                                         request_type='partnership', order=2)
        html = self.html()
        self.assertIn('Форматы <span class="mark">', html)
        self.assertIn('id="z-rev-top"', html)          # рост дохода и доля ZEA
        self.assertIn('ЗАДАНИЕ', html)                 # этапы до сдачи
        self.assertNotIn('Два формата', html)

    def test_cards_show_cover_and_modal_shows_product(self):
        p = Project.objects.create(name='Продукт', description='d', project_type='CRM', technologies='Django',
                                   image='projects/shot.webp')
        html = self.html()
        card = html.split('<template id="project-detail-%d">' % p.pk)[0]
        self.assertNotIn('projects/shot.webp', card)        # на главной — обложка
        self.assertIn('class="cover grain"', card)
        detail = html.split('<template id="project-detail-%d">' % p.pk)[1].split('</template>')[0]
        self.assertIn('projects/shot.webp', detail)         # в «Подробнее» — сам продукт

    def test_more_projects_button(self):
        for i in range(9):
            Project.objects.create(name=f'Кейс {i}', description='d', project_type='CRM', technologies='Django')
        html = self.html()
        self.assertIn('id="projects-more"', html)
        self.assertEqual(html.count('class="p-card p-more"'), 2)


class PartnerPagesTests(TestCase):
    def setUp(self):
        self.p = Partner.objects.create(name='Тёплый город', industry='Ритейл', about='Магазин отопления',
                                        website='https://example.kg')
        Project.objects.create(name='Магазин', description='d', project_type='Сайт', technologies='Django',
                               partner=self.p)
        Partner.objects.create(name='Скрытый', industry='x', is_active=False)

    def test_slug_generated_from_cyrillic(self):
        self.assertEqual(self.p.slug, 'teplyy-gorod')
        self.assertEqual(self.p.get_absolute_url(), '/partners/teplyy-gorod/')

    def test_list_and_detail(self):
        html = self.client.get('/partners/').content.decode()
        self.assertIn('href="/partners/teplyy-gorod/"', html)
        self.assertNotIn('Скрытый', html)
        detail = self.client.get('/partners/teplyy-gorod/')
        self.assertEqual(detail.status_code, 200)
        page = detail.content.decode()
        for text in ('Магазин отопления', 'https://example.kg', '<template id="project-detail-', 'id="project-modal"'):
            self.assertIn(text, page)
        self.assertIn('href="/en/partners/teplyy-gorod/"', page)   # язык переключает эту же страницу
        self.assertIn('href="/#contact"', page)                    # меню ведёт на главную

    def test_inactive_partner_404(self):
        hidden = Partner.objects.get(name='Скрытый')
        self.assertEqual(self.client.get(f'/partners/{hidden.slug}/').status_code, 404)

    def test_menu_and_sitemap(self):
        self.assertIn('href="/partners/"', self.client.get('/').content.decode())
        self.assertIn('/partners/teplyy-gorod/', self.client.get('/sitemap.xml').content.decode())


class ContactsVisibilityTests(TestCase):
    def test_empty_contacts_not_rendered(self):
        html = self.client.get('/').content.decode()
        for needle in ('wa.me', 't.me/', 'instagram.com', 'mailto:', 'hello@zea.dev'):
            self.assertNotIn(needle, html)

    def test_filled_contact_rendered(self):
        s = SiteSettings.get()
        s.telegram_url = 'https://t.me/real_zea'
        s.save()
        html = self.client.get('/').content.decode()
        self.assertIn('https://t.me/real_zea', html)
        self.assertNotIn('wa.me', html)


class SeoTests(TestCase):
    def test_meta_and_https_urls(self):
        html = self.client.get('/').content.decode()
        self.assertIn('<title>ZEA — технологический партнёр для бизнеса · Разработка и сопровождение</title>', html)
        self.assertIn('ZEA берёт на себя технологическую часть бизнеса', html)
        self.assertIn('<link rel="canonical" href="https://zeastudio.su/">', html)
        self.assertIn('<meta property="og:url" content="https://zeastudio.su/">', html)
        self.assertIn('<meta property="og:locale" content="ru_RU">', html)
        self.assertIn('<meta property="og:locale:alternate" content="ky_KG">', html)
        self.assertIn('hreflang="en" href="https://zeastudio.su/en/"', html)

    def test_localized_meta(self):
        html = self.client.get('/en/').content.decode()
        self.assertIn('<meta property="og:locale" content="en_US">', html)
        self.assertIn('<link rel="canonical" href="https://zeastudio.su/en/">', html)
        self.assertIn('ZEA — Technology Partner for Business', html)

    def test_no_images_when_not_set(self):
        html = self.client.get('/').content.decode()
        self.assertNotIn('og:image', html)
        self.assertNotIn('rel="icon"', html)
        self.assertNotIn('"logo"', html)

    def test_jsonld_valid(self):
        html = self.client.get('/').content.decode()
        raw = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        data = json.loads(raw)
        self.assertEqual(data['@type'], 'Organization')
        self.assertEqual(data['url'], 'https://zeastudio.su/')
        self.assertNotIn('sameAs', data)

    def test_robots_and_sitemap_https(self):
        robots = self.client.get('/robots.txt').content.decode()
        self.assertIn('Sitemap: https://zeastudio.su/sitemap.xml', robots)
        self.assertIn('Disallow: /hub/', robots)
        sitemap = self.client.get('/sitemap.xml').content.decode()
        for loc in ('https://zeastudio.su/', 'https://zeastudio.su/ky/', 'https://zeastudio.su/en/'):
            self.assertIn(f'<loc>{loc}</loc>', sitemap)
        self.assertNotIn('http://zeastudio', sitemap)


class TailwindTests(TestCase):
    def setUp(self):
        site_views._TAILWIND_CSS = None

    def tearDown(self):
        site_views._TAILWIND_CSS = None

    def test_css_inlined(self):
        html = self.client.get('/').content.decode()
        self.assertIn('tailwindcss v3.4.17', html)
        self.assertIn('.gap-5{', html)

    def test_works_without_collectstatic(self):
        """Чистый clone: STATIC_ROOT пустой — CSS берётся из app/static через finders."""
        with tempfile.TemporaryDirectory() as empty_root, override_settings(STATIC_ROOT=empty_root):
            site_views._TAILWIND_CSS = None
            self.assertIn('tailwindcss v3.4.17', site_views._tailwind_inline())
