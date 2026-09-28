"""CMS публичного сайта: утверждённый контент, безопасное заполнение, новые поля."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.cms import site_content
from apps.cms.models import (
    Commitment, CooperationFormat, Partner, ProcessStep, Project, Service,
    SiteSettings, Stat, WhyUs,
)

LIST_MODELS = {'Commitment': Commitment, 'CooperationFormat': CooperationFormat,
               'ProcessStep': ProcessStep, 'Service': Service, 'WhyUs': WhyUs}


class SeedMigrationTests(TestCase):
    """Миграция 0010 уже применена к тестовой БД — проверяем её результат."""

    def test_list_blocks_seeded(self):
        self.assertEqual(Commitment.objects.count(), 6)
        self.assertEqual(ProcessStep.objects.count(), 6)
        self.assertEqual(Service.objects.count(), 7)
        self.assertEqual(WhyUs.objects.count(), 5)
        formats = list(CooperationFormat.objects.all())
        self.assertEqual([f.request_type for f in formats], ['partnership', 'development'])
        self.assertTrue(formats[0].is_primary)
        self.assertFalse(formats[1].is_primary)

    def test_unverified_content_not_seeded(self):
        self.assertFalse(Project.objects.exists())
        self.assertFalse(Partner.objects.exists())
        self.assertFalse(Stat.objects.exists())

    def test_all_languages_filled(self):
        for step in ProcessStep.objects.all():
            for lang in ('ru', 'ky', 'en'):
                self.assertTrue(getattr(step, f'title_{lang}'))
        fmt = CooperationFormat.objects.get(request_type='partnership')
        self.assertEqual(fmt.cta_label_en, 'Discuss a partnership')
        self.assertEqual(fmt.title_ky, 'Технологиялык өнөктөштүк')

    def test_no_percentages_published(self):
        for f in CooperationFormat.objects.all():
            for lang in ('ru', 'ky', 'en'):
                text = ' '.join(filter(None, [getattr(f, f'{fld}_{lang}') for fld in
                                              ('title', 'audience', 'description', 'terms')]))
                self.assertNotIn('%', text)


class SeedSiteSettingsTests(TestCase):
    def _legacy_row(self):
        """Строка как на production: старые дефолты модели и заглушки контактов."""
        SiteSettings.objects.all().delete()
        s = SiteSettings(pk=1)
        legacy = {
            'site_tagline': 'IT Studio',
            'hero_badge': 'Открыты для новых проектов',
            'hero_title': 'ZEA — разработка цифровых решений для бизнеса',
            'about_text': next(v for v in site_content.LEGACY_VALUES['about_text']
                               if v.startswith('ZEA — мини')),
            'footer_text': '© 2024 ZEA IT Studio. All rights reserved.',
        }
        for field, value in legacy.items():
            for col in (field, f'{field}_ru', f'{field}_ky', f'{field}_en'):
                setattr(s, col, value)
        for field, value in site_content.PLACEHOLDER_CONTACTS.items():
            setattr(s, field, value)
        s.site_domain = ''
        s.save()
        return s

    def test_legacy_defaults_replaced(self):
        self._legacy_row()
        site_content.seed_site_settings(SiteSettings)
        s = SiteSettings.objects.get(pk=1)
        self.assertEqual(s.hero_title_ru, 'ZEA — технологический партнёр для бизнеса')
        self.assertEqual(s.hero_title_ky, 'ZEA — бизнес үчүн технологиялык өнөктөш')
        self.assertEqual(s.hero_title_en, 'ZEA — a technology partner for business')
        self.assertNotIn('мини IT-студия', s.about_text_ru)
        self.assertEqual(s.footer_text_ru, '')
        self.assertEqual(s.site_domain, 'https://zeastudio.su')

    def test_placeholder_contacts_cleared(self):
        self._legacy_row()
        site_content.seed_site_settings(SiteSettings)
        s = SiteSettings.objects.get(pk=1)
        self.assertEqual((s.telegram_url, s.whatsapp_url, s.instagram_url, s.email), ('', '', '', ''))

    def test_manual_edits_preserved(self):
        s = self._legacy_row()
        s.hero_title_ru = s.hero_title = 'Свой заголовок'
        s.whatsapp_url = 'https://wa.me/996555000111'
        s.site_domain = 'https://example.org'
        s.save()
        site_content.seed_site_settings(SiteSettings)
        s = SiteSettings.objects.get(pk=1)
        self.assertEqual(s.hero_title_ru, 'Свой заголовок')
        self.assertEqual(s.whatsapp_url, 'https://wa.me/996555000111')
        self.assertEqual(s.site_domain, 'https://example.org')

    def test_force_overwrites(self):
        s = SiteSettings.get()
        s.hero_title_ru = 'Свой заголовок'
        s.save()
        site_content.seed_site_settings(SiteSettings, force=True)
        self.assertEqual(SiteSettings.get().hero_title_ru, 'ZEA — технологический партнёр для бизнеса')


class SeedListBlocksTests(TestCase):
    def test_if_empty_skips_filled_tables(self):
        Service.objects.filter(order__gt=1).delete()
        Service.objects.update(title_ru='Своя услуга', title='Своя услуга')
        site_content.seed_list_blocks(LIST_MODELS, mode='if_empty')
        self.assertEqual(list(Service.objects.values_list('title_ru', flat=True)), ['Своя услуга'])

    def test_missing_mode_is_idempotent_and_never_deletes(self):
        custom = Service.objects.create(title='Моя услуга', title_ru='Моя услуга', description='x')
        before = {name: m.objects.count() for name, m in LIST_MODELS.items()}
        site_content.seed_list_blocks(LIST_MODELS, mode='missing')
        site_content.seed_list_blocks(LIST_MODELS, mode='missing')
        after = {name: m.objects.count() for name, m in LIST_MODELS.items()}
        self.assertEqual(before, after)
        self.assertTrue(Service.objects.filter(pk=custom.pk).exists())

    def test_missing_mode_restores_removed_item(self):
        ProcessStep.objects.filter(title_ru='Анализ').delete()
        site_content.seed_list_blocks(LIST_MODELS, mode='missing')
        self.assertTrue(ProcessStep.objects.filter(title_ru='Анализ').exists())

    def test_update_mode_rewrites_text(self):
        Commitment.objects.filter(title_ru='Анализ').update(description_ru='старое')
        site_content.seed_list_blocks(LIST_MODELS, mode='update')
        self.assertIn('процессах бизнеса', Commitment.objects.get(title_ru='Анализ').description_ru)


class PopulateDbCommandTests(TestCase):
    def test_does_not_delete_anything(self):
        project = Project.objects.create(name='Реальный проект', description='d', project_type='CRM',
                                         technologies='Django')
        partner = Partner.objects.create(name='Клиент', industry='Логистика')
        stat = Stat.objects.create(value_text='5', label='проектов')
        call_command('populate_db', stdout=StringIO())
        call_command('populate_db', '--update', stdout=StringIO())
        for obj in (project, partner, stat):
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())
        self.assertEqual(Service.objects.count(), 7)


class ModelFieldsTests(TestCase):
    def test_project_case_fields(self):
        p = Project.objects.create(name='P', description='d', project_type='t', technologies='A, B',
                                   task='T', solution='S', result='R', is_featured=True)
        p.refresh_from_db()
        self.assertEqual((p.task, p.solution, p.result, p.is_featured), ('T', 'S', 'R', True))

    def test_stat_is_active_default(self):
        self.assertTrue(Stat.objects.create(value_text='1', label='x').is_active)

    def test_admin_names_distinguish_from_hub(self):
        self.assertEqual(Project._meta.verbose_name_plural, 'Проекты сайта (кейсы)')
        self.assertEqual(Partner._meta.verbose_name_plural, 'Партнёры сайта (логотипы)')

    def test_contact_defaults_are_empty(self):
        SiteSettings.objects.all().delete()
        s = SiteSettings.get()
        self.assertEqual((s.telegram_url, s.whatsapp_url, s.instagram_url, s.email), ('', '', '', ''))
