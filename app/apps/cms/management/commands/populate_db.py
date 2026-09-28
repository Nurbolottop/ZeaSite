"""Безопасное заполнение публичного сайта утверждённым контентом.

НИЧЕГО не удаляет. Проекты, партнёров и статистику не создаёт — их вносят
вручную через админку только после проверки.

  python manage.py populate_db            # создать недостающее, существующее не трогать
  python manage.py populate_db --update   # + перезаписать тексты утверждёнными
"""
from django.core.management.base import BaseCommand
from django.utils import translation

from apps.cms import models as cms_models
from apps.cms import site_content


class Command(BaseCommand):
    help = 'Заполняет сайт утверждённым контентом (без удаления данных)'

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store_true',
                            help='Перезаписать существующие тексты утверждёнными')

    def handle(self, *args, **options):
        update = options['update']
        models = {name: getattr(cms_models, name) for name, _ in site_content.LIST_BLOCKS}
        with translation.override('ru'):
            site_content.seed_site_settings(cms_models.SiteSettings, force=update,
                                            log=self.stdout.write)
            site_content.seed_list_blocks(models, mode='update' if update else 'missing',
                                          log=self.stdout.write)
        self.stdout.write(self.style.SUCCESS('Готово. Данные не удалялись.'))
