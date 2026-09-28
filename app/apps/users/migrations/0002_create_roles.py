from django.db import migrations

# Имена зафиксированы здесь, а не импортом из apps.users.roles:
# миграция должна давать одинаковый результат независимо от будущих правок кода.
ROLE_NAMES = (
    'Руководитель / Финансы и аналитика',
    'Менеджер по развитию',
    'Проектный менеджер (PM)',
    'Технический руководитель',
    'Маркетинг / Бренд',
    'DevOps',
)


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ROLE_NAMES:
        Group.objects.get_or_create(name=name)


def delete_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=ROLE_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
