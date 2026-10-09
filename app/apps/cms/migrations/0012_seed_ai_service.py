"""Добавляет направление «AI и ассистенты», если его ещё нет.

Безопасно для production: ничего не удаляет и не меняет существующие услуги.
"""
from django.db import migrations

from apps.cms import site_content

AI_TITLE = 'AI и ассистенты'


def forwards(apps, schema_editor):
    Service = apps.get_model('cms', 'Service')
    if Service.objects.filter(title_ru=AI_TITLE).exists():
        return
    item = next(i for i in site_content.SERVICES if i['title']['ru'] == AI_TITLE)
    obj = Service(order=(Service.objects.count() + 1), is_active=True)
    for key, value in item.items():
        if key in site_content.TRANSLATED['Service']:
            site_content._set_ml(obj, key, value)
        else:
            setattr(obj, key, value)
    obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_redesign_media'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
