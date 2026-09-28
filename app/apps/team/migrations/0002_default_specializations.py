from django.db import migrations

# Начальный справочник. Дальше расширяется в админке (без миграций).
# (название, техническая, порядок)
DEFAULTS = (
    ('Backend Developer', True, 10),
    ('Frontend Developer', True, 20),
    ('Mobile Developer', True, 30),
    ('UI/UX Designer', False, 40),
    ('QA / Tester', True, 50),
    ('DevOps', True, 60),
    ('Project Manager', False, 70),
    ('Technical Lead', True, 80),
)


def create(apps, schema_editor):
    Specialization = apps.get_model('team', 'Specialization')
    for name, technical, order in DEFAULTS:
        Specialization.objects.get_or_create(
            name=name, defaults={'is_technical': technical, 'sort_order': order})


def remove(apps, schema_editor):
    apps.get_model('team', 'Specialization').objects.filter(
        name__in=[d[0] for d in DEFAULTS], employees__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [('team', '0001_initial')]
    operations = [migrations.RunPython(create, remove)]
