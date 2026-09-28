"""Заполняет новую структуру сайта утверждённым контентом.

Безопасно для production:
  * ничего не удаляет;
  * блоки-списки создаются, только если таблица пустая;
  * тексты SiteSettings меняются, только если там пусто или старый дефолт;
  * очищаются только заведомые заглушки контактов (wa.me/996700000000 и т.п.);
  * проекты, партнёры и статистику НЕ создаёт.
"""
from django.db import migrations

from apps.cms import site_content


def forwards(apps, schema_editor):
    models = {name: apps.get_model('cms', name) for name, _ in site_content.LIST_BLOCKS}
    site_content.seed_site_settings(apps.get_model('cms', 'SiteSettings'))
    site_content.seed_list_blocks(models, mode='if_empty')


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0009_partnership_blocks'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
