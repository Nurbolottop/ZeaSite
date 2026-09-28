from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.contracts.models import ContractStatus
from apps.projects import services
from apps.projects.models import Project, ProjectMember, ProjectStatus, ProjectTechnicalInfo

from .utils import S, Team, make_company, make_project, move_to, spec

P = ProjectStatus


class CreateProjectTests(TestCase):
    def setUp(self):
        self.t = Team()

    def test_created_for_partner_with_history(self):
        p = self.t.project
        self.assertEqual((p.status, p.company, p.created_by), (P.PLANNING, self.t.company, self.t.head))
        entry = p.status_history.get()
        self.assertEqual((entry.from_status, entry.to_status), ('', P.PLANNING))

    def test_only_partner_with_active_contract(self):
        t = self.t
        # компания на стадии «Договор» с черновиком — не партнёр
        candidate = move_to(make_company(t.head, name='Кандидат'), S.CONTRACT, t.head)
        from apps.contracts.models import Contract
        draft = Contract.objects.create(company=candidate, number='D-1', title='x')
        with self.assertRaises(ValidationError):
            make_project(t.head, draft, t.pm, t.lead, code='X-1')
        # договор партнёра истёк → новый проект по нему нельзя
        Contract.objects.filter(pk=t.contract.pk).update(status=ContractStatus.EXPIRED)
        t.contract.refresh_from_db()
        with self.assertRaises(ValidationError):
            make_project(t.head, t.contract, t.pm, t.lead, code='X-2')

    def test_company_taken_from_contract(self):
        other = make_company(self.t.head, name='Чужая')
        project = Project(contract=self.t.contract, company=other, name='x', code='X-3', project_type='crm',
                          pm=self.t.pm, technical_lead=self.t.lead)
        services.create_project(project=project, user=self.t.head)
        self.assertEqual(project.company, self.t.company)

    def test_wrong_roles_for_pm_and_lead(self):
        t = self.t
        for pm, lead in ((t.lead, t.lead), (t.pm, t.pm), (t.bizdev, t.lead), (t.pm, t.devops)):
            with self.assertRaises(ValidationError, msg=(pm, lead)):
                make_project(t.head, t.contract, pm, lead, code='BAD-1')
        t.pm.is_active = False
        t.pm.save()
        with self.assertRaises(ValidationError):
            make_project(t.head, t.contract, t.pm, t.lead, code='BAD-2')

    def test_only_head_creates(self):
        t = self.t
        for user in (t.bizdev, t.pm, t.lead, t.marketing, t.devops):
            with self.assertRaises(PermissionDenied):
                make_project(user, t.contract, t.pm, t.lead, code='NO-1')

    def test_other_type_needs_description_and_dates(self):
        t = self.t
        with self.assertRaises(ValidationError):
            make_project(t.head, t.contract, t.pm, t.lead, code='O-1', project_type='other')
        with self.assertRaises(ValidationError):
            make_project(t.head, t.contract, t.pm, t.lead, code='O-2', start_date=date(2027, 5, 1),
                         planned_end_date=date(2027, 1, 1))
        p = make_project(t.head, t.contract, t.pm, t.lead, code='O-3', project_type='other',
                         project_type_other='Чат-бот поддержки')
        self.assertEqual(p.type_display, 'Чат-бот поддержки')


class UpdateProjectTests(TestCase):
    def setUp(self):
        self.t = Team()

    def test_pm_edits_work_fields_only(self):
        t, p = self.t, self.t.project
        p.priority, p.notes = 'high', 'Созвон по четвергам'
        services.update_project(project=p, user=t.pm)
        for field, value in (('pm', t.pm2), ('technical_lead', t.lead2), ('name', 'Другое'), ('code', 'ZZ')):
            fresh = Project.objects.get(pk=p.pk)
            setattr(fresh, field, value)
            with self.assertRaises(PermissionDenied, msg=field):
                services.update_project(project=fresh, user=t.pm)
        p.refresh_from_db()
        self.assertEqual((p.priority, p.pm, p.technical_lead), ('high', t.pm, t.lead))

    def test_pm_cannot_edit_foreign_project(self):
        p = self.t.other
        p.notes = 'чужие заметки'
        with self.assertRaises(PermissionDenied):
            services.update_project(project=p, user=self.t.pm)

    def test_pm_cannot_assign_himself(self):
        p = self.t.other
        p.pm = self.t.pm
        with self.assertRaises(PermissionDenied):
            services.update_project(project=p, user=self.t.pm)

    def test_head_reassigns_with_role_check(self):
        t, p = self.t, self.t.project
        p.pm, p.technical_lead = t.pm2, t.lead2
        services.update_project(project=p, user=t.head)
        p.refresh_from_db()
        self.assertEqual((p.pm, p.technical_lead), (t.pm2, t.lead2))
        p.pm = t.bizdev
        with self.assertRaises(ValidationError):
            services.update_project(project=p, user=t.head)

    def test_tech_lead_and_others_cannot_edit_card(self):
        p = self.t.project
        p.notes = 'x'
        for user in (self.t.lead, self.t.bizdev, self.t.devops, self.t.marketing):
            with self.assertRaises(PermissionDenied, msg=user):
                services.update_project(project=p, user=user)


class StatusTests(TestCase):
    def setUp(self):
        self.t = Team()
        self.p = self.t.project

    def go(self, status, user=None, comment=''):
        return services.change_project_status(project=self.p, to_status=status,
                                              user=user or self.t.pm, comment=comment)

    def test_main_path_and_history(self):
        for status in (P.DEVELOPMENT, P.TESTING, P.MVP, P.LAUNCHED, P.SUPPORT):
            self.go(status)
        self.p.refresh_from_db()
        self.assertEqual(self.p.status, P.SUPPORT)
        self.assertEqual(self.p.launch_date, date.today())
        chain = list(self.p.status_history.order_by('changed_at', 'id').values_list('to_status', flat=True))
        self.assertEqual(chain, [P.PLANNING, P.DEVELOPMENT, P.TESTING, P.MVP, P.LAUNCHED, P.SUPPORT])

    def test_allowed_returns(self):
        self.go(P.DEVELOPMENT)
        self.go(P.TESTING)
        self.go(P.DEVELOPMENT)       # Тестирование → Разработка
        self.go(P.TESTING)
        self.go(P.MVP)
        self.go(P.TESTING)           # MVP → Тестирование
        self.go(P.MVP)
        self.go(P.DEVELOPMENT)       # MVP → Разработка
        self.assertEqual(self.p.status, P.DEVELOPMENT)

    def test_invalid_transitions(self):
        for target in (P.TESTING, P.MVP, P.LAUNCHED, P.SUPPORT, 'bogus'):
            with self.assertRaises(ValidationError, msg=target):
                self.go(target)
        self.go(P.DEVELOPMENT)
        with self.assertRaises(ValidationError):
            self.go(P.PLANNING)
        self.assertEqual(Project.objects.get(pk=self.p.pk).status, P.DEVELOPMENT)

    def test_pause_requires_reason_and_resumes_to_previous(self):
        self.go(P.DEVELOPMENT)
        self.go(P.TESTING)
        with self.assertRaises(ValidationError):
            self.go(P.PAUSED)
        self.go(P.PAUSED, comment='Партнёр взял паузу на месяц')
        self.p.refresh_from_db()
        self.assertEqual((self.p.status, self.p.paused_from_status), (P.PAUSED, P.TESTING))
        # из паузы — только в прежний статус (или отмена руководителем)
        self.assertEqual(services.allowed_transitions(self.p, self.t.pm), (P.TESTING,))
        with self.assertRaises(ValidationError):
            self.go(P.DEVELOPMENT)
        self.go(P.TESTING, comment='Возобновили')
        self.p.refresh_from_db()
        self.assertEqual((self.p.status, self.p.paused_from_status), (P.TESTING, ''))

    def test_cancel_only_head_with_reason(self):
        with self.assertRaises(PermissionDenied):
            self.go(P.CANCELLED, comment='x')
        with self.assertRaises(ValidationError):
            self.go(P.CANCELLED, user=self.t.head)
        self.go(P.CANCELLED, user=self.t.head, comment='Партнёр отказался от проекта')
        self.assertTrue(Project.objects.filter(pk=self.p.pk).exists())
        self.assertEqual(services.allowed_transitions(self.p, self.t.head), ())

    def test_cancel_from_pause(self):
        self.go(P.PAUSED, comment='Пауза')
        self.go(P.CANCELLED, user=self.t.head, comment='Не вернулись')
        self.assertEqual(self.p.status, P.CANCELLED)

    def test_who_changes_status(self):
        for user in (self.t.lead, self.t.bizdev, self.t.marketing, self.t.devops, self.t.pm2):
            with self.assertRaises(PermissionDenied, msg=user):
                self.go(P.DEVELOPMENT, user=user)
        self.go(P.DEVELOPMENT, user=self.t.head)


class MemberTests(TestCase):
    def setUp(self):
        self.t = Team()

    def add(self, user, member, spec_name, project=None):
        return services.add_member(project=project or self.t.project, member=member,
                                   specialization=spec(spec_name), user=user)

    def test_many_members_and_many_projects(self):
        t = self.t
        self.add(t.pm, t.dev, 'Backend Developer')
        self.add(t.pm, t.devops, 'DevOps')
        self.add(t.head, t.dev, 'Backend Developer', project=t.other)
        self.assertEqual(t.project.members.filter(is_active=True).count(), 2)
        self.assertEqual(ProjectMember.objects.filter(member=t.dev, is_active=True).count(), 2)

    def test_no_duplicate_active_role(self):
        self.add(self.t.pm, self.t.dev, 'Backend Developer')
        with self.assertRaises(ValidationError):
            self.add(self.t.pm, self.t.dev, 'Backend Developer')
        self.add(self.t.pm, self.t.dev, 'QA / Tester')  # другая роль — можно

    def test_remove_keeps_history_and_allows_rejoin(self):
        m = self.add(self.t.pm, self.t.dev, 'Backend Developer')
        services.remove_member(membership=m, user=self.t.pm)
        m.refresh_from_db()
        self.assertEqual((m.is_active, m.left_at), (False, date.today()))
        self.add(self.t.pm, self.t.dev, 'Backend Developer')
        self.assertEqual(ProjectMember.objects.filter(member=self.t.dev).count(), 2)

    def test_tech_lead_manages_only_technical(self):
        t = self.t
        m = self.add(t.lead, t.dev, 'Backend Developer')
        with self.assertRaises(PermissionDenied):
            self.add(t.lead, t.dev, 'UI/UX Designer')
        design = self.add(t.pm, t.dev, 'UI/UX Designer')
        with self.assertRaises(PermissionDenied):
            services.remove_member(membership=design, user=t.lead)
        services.remove_member(membership=m, user=t.lead)

    def test_foreign_or_outsiders_cannot_manage(self):
        t = self.t
        for user in (t.pm2, t.lead2, t.bizdev, t.marketing, t.devops):
            with self.assertRaises(PermissionDenied, msg=user):
                self.add(user, t.dev, 'Backend Developer')

    def test_only_active_employees(self):
        t = self.t
        with self.assertRaises(ValidationError):
            self.add(t.head, t.bizdev, 'Backend Developer')  # нет профиля сотрудника
        t.dev.employee.is_active = False
        t.dev.employee.save()
        with self.assertRaises(ValidationError):
            self.add(t.head, t.dev, 'Backend Developer')


class TechnicalInfoTests(TestCase):
    def setUp(self):
        self.t = Team()

    def save(self, user, **fields):
        info = ProjectTechnicalInfo(project=self.t.project, **fields)
        return services.save_technical_info(info=info, user=user)

    def test_editors(self):
        self.save(self.t.lead, repository_url='https://github.com/zea/crm', technology_stack='Django')
        for user in (self.t.devops, self.t.bizdev, self.t.marketing, self.t.pm2):
            with self.assertRaises(PermissionDenied):
                self.save(user, technology_stack='x')

    def test_secrets_rejected(self):
        secrets = {
            'server_info': 'root password: Qwerty123',
            'deployment_notes': '-----BEGIN OPENSSH PRIVATE KEY-----\nabc',
            'technical_notes': 'токен=abcdef123456',
            'technology_stack': 'ghp_' + 'a' * 36,
            'repository_url': 'https://user:secretpass@github.com/zea/crm',
        }
        for field, value in secrets.items():
            with self.assertRaises(ValidationError, msg=field) as ctx:
                self.save(self.t.head, **{field: value})
            self.assertIn(field, ctx.exception.error_dict)
        self.assertFalse(ProjectTechnicalInfo.objects.exists())

    def test_normal_text_allowed(self):
        info = self.save(self.t.head, server_info='Hetzner CX22, Ubuntu 24.04, доступ по SSH-ключам из 1Password',
                         deployment_notes='docker compose up -d; миграции применяются автоматически')
        self.assertTrue(info.pk)
