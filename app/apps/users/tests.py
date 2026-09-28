from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from apps.hub.navigation import NAVIGATION

from .access import MODULE_ACCESS, can_access_module, get_user_roles, has_role
from .models import HubProfile
from .profile import get_hub_profile, initials
from .roles import ALL_ROLES, Role


class RolesTests(TestCase):
    def test_all_roles_created_by_migration(self):
        self.assertTrue(set(ALL_ROLES) <= set(Group.objects.values_list('name', flat=True)))

    def test_user_can_have_several_roles(self):
        user = User.objects.create_user('multi', password='x')
        user.groups.add(*Group.objects.filter(name__in=[Role.PM, Role.DEVOPS]))
        user = User.objects.get(pk=user.pk)
        self.assertEqual(get_user_roles(user), [Role.PM, Role.DEVOPS])
        self.assertTrue(has_role(user, Role.DEVOPS))
        self.assertFalse(has_role(user, Role.HEAD))

    def test_superuser_has_every_role(self):
        admin = User.objects.create_superuser('root', password='x')
        self.assertTrue(has_role(admin, Role.HEAD))
        self.assertTrue(all(can_access_module(admin, m) for m in MODULE_ACCESS))

    def test_inactive_user_has_no_access(self):
        user = User.objects.create_user('off', password='x', is_active=False)
        user.groups.add(Group.objects.get(name=Role.HEAD))
        self.assertFalse(has_role(user, Role.HEAD))

    def test_every_nav_item_is_in_access_matrix(self):
        for item in NAVIGATION:
            self.assertIn(item.module, MODULE_ACCESS)


class HubProfileTests(TestCase):
    def test_profile_is_optional(self):
        user = User.objects.create_user('ivan', password='x', first_name='Иван', last_name='Петров')
        self.assertIsNone(get_hub_profile(user))
        self.assertEqual(initials(user), 'ИП')
        HubProfile.objects.create(user=user, phone='+996')
        user = User.objects.get(pk=user.pk)
        self.assertEqual(get_hub_profile(user).phone, '+996')


class AdminUserTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('root', password='x')
        self.client.force_login(self.admin)

    def test_create_user_with_roles_and_profile_via_admin(self):
        pm, devops = Group.objects.get(name=Role.PM), Group.objects.get(name=Role.DEVOPS)
        resp = self.client.post(reverse('admin:auth_user_add'), {
            'username': 'new_pm',
            'usable_password': 'true',
            'password1': 'Str0ng-pass-987',
            'password2': 'Str0ng-pass-987',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'email': 'ivan@example.com',
            'is_active': 'on',
            'groups': [pm.pk, devops.pk],
            'hub_profile-TOTAL_FORMS': '1',
            'hub_profile-INITIAL_FORMS': '0',
            'hub_profile-MIN_NUM_FORMS': '0',
            'hub_profile-MAX_NUM_FORMS': '1',
            'hub_profile-0-phone': '+996 555 000 000',
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username='new_pm')
        self.assertEqual(user.hub_profile.phone, '+996 555 000 000')
        self.assertEqual(get_user_roles(user), [Role.PM, Role.DEVOPS])
        self.assertTrue(self.client.login(username='new_pm', password='Str0ng-pass-987'))

    def test_deactivate_action(self):
        user = User.objects.create_user('temp', password='x')
        self.client.post(reverse('admin:auth_user_changelist'), {
            'action': 'deactivate_users', '_selected_action': [user.pk, self.admin.pk],
        })
        user.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertTrue(self.admin.is_active)  # себя деактивировать нельзя
