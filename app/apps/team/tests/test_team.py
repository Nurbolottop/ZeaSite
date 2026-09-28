from django.contrib.auth.models import User
from django.test import TestCase

from apps.projects import services as project_services
from apps.projects.tests.utils import Team, spec
from apps.team.models import EmployeeProfile, Specialization


class TeamTests(TestCase):
    def setUp(self):
        self.t = Team()
        project_services.add_member(project=self.t.project, member=self.t.dev,
                                    specialization=spec('Backend Developer'), user=self.t.head)
        project_services.add_member(project=self.t.other, member=self.t.dev,
                                    specialization=spec('QA / Tester'), user=self.t.head)

    def test_default_specializations(self):
        names = set(Specialization.objects.values_list('name', flat=True))
        self.assertTrue({'Backend Developer', 'Frontend Developer', 'Mobile Developer', 'UI/UX Designer',
                         'QA / Tester', 'DevOps', 'Project Manager', 'Technical Lead'} <= names)
        self.assertFalse(Specialization.objects.get(name='UI/UX Designer').is_technical)

    def test_access(self):
        t = self.t
        for user, code in ((t.head, 200), (t.pm, 200), (t.lead, 200), (t.bizdev, 403), (t.marketing, 403),
                           (t.devops, 403), (t.nobody, 403)):
            self.client.force_login(user)
            self.assertEqual(self.client.get('/hub/team/').status_code, code, user)
        self.client.force_login(t.pm)
        self.assertEqual(self.client.get('/hub/team/add/').status_code, 403)

    def test_list_workload_and_roles(self):
        self.client.force_login(self.t.head)
        resp = self.client.get('/hub/team/')
        dev = next(e for e in resp.context['employees'] if e.user == self.t.dev)
        self.assertEqual(dev.active_projects_count, 2)
        self.assertContains(resp, 'Активных проектов: 2')
        self.assertContains(resp, 'Backend Developer')
        self.assertContains(resp, 'нет роли')          # специализация есть, роли доступа нет
        pm = next(e for e in resp.context['employees'] if e.user == self.t.pm)
        self.assertEqual(pm.active_projects_count, 1)  # PM проекта считается как занятость
        self.assertIn('Проектный менеджер (PM)', pm.hub_roles)

    def test_employee_card(self):
        self.client.force_login(self.t.pm)
        resp = self.client.get(f'/hub/team/{self.t.dev.employee.pk}/')
        self.assertContains(resp, 'Активных проектов: 2')
        self.assertContains(resp, 'История участия')
        # свой проект — ссылкой, чужой — только название
        self.assertContains(resp, f'/hub/projects/{self.t.project.pk}/')
        self.assertNotContains(resp, f'/hub/projects/{self.t.other.pk}/')
        self.assertContains(resp, 'Telegram-бот')

    def test_head_creates_employee(self):
        new = User.objects.create_user('front', password='x', first_name='Фронт')
        self.client.force_login(self.t.head)
        spec_ids = list(Specialization.objects.filter(name__in=['Frontend Developer', 'UI/UX Designer'])
                        .values_list('pk', flat=True))
        resp = self.client.post('/hub/team/add/', {'user': new.pk, 'position': 'Frontend', 'employment_type': 'part_time',
                                                   'specializations': spec_ids, 'is_active': 'on'})
        profile = EmployeeProfile.objects.get(user=new)
        self.assertRedirects(resp, f'/hub/team/{profile.pk}/')
        self.assertEqual(profile.specializations.count(), 2)
        # повторно тот же пользователь недоступен
        form = self.client.get('/hub/team/add/').context['form']
        self.assertNotIn(new, form.fields['user'].queryset)

    def test_roles_and_specializations_are_separate(self):
        """Группа доступа DevOps ≠ специализация DevOps: одно не создаёт другое."""
        self.assertFalse(self.t.bizdev.groups.filter(name='DevOps').exists())
        self.assertEqual(self.t.dev.groups.count(), 0)
        self.assertTrue(self.t.dev.employee.specializations.exists())
