from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from apps.projects import services
from apps.projects.models import Project, ProjectStatus, ProjectTechnicalInfo

from .utils import Team, make_project, spec

P = ProjectStatus


class ProjectAccessTests(TestCase):
    def setUp(self):
        self.t = Team()
        t = self.t
        services.add_member(project=t.project, member=t.devops, specialization=spec('DevOps'), user=t.head)
        services.save_technical_info(info=ProjectTechnicalInfo(
            project=t.project, repository_url='https://github.com/zea/ke-crm',
            server_info='Hetzner CX22'), user=t.head)
        t.project.notes = 'Внутренняя заметка: сложный клиент'
        services.update_project(project=t.project, user=t.head)

    def visible(self, user):
        self.client.force_login(user)
        resp = self.client.get('/hub/projects/')
        return resp.status_code, {p.code for p in resp.context['projects']} if resp.status_code == 200 else None

    def test_list_scope_by_role(self):
        t = self.t
        both = {'KE-CRM', 'KE-BOT'}
        self.assertEqual(self.visible(t.head), (200, both))
        self.assertEqual(self.visible(t.bizdev), (200, both))
        self.assertEqual(self.visible(t.marketing), (200, both))
        self.assertEqual(self.visible(t.pm), (200, {'KE-CRM'}))
        self.assertEqual(self.visible(t.pm2), (200, {'KE-BOT'}))
        self.assertEqual(self.visible(t.lead), (200, {'KE-CRM'}))
        self.assertEqual(self.visible(t.devops), (200, {'KE-CRM'}))
        self.assertEqual(self.visible(t.devops2), (200, set()))
        self.assertEqual(self.visible(t.nobody), (403, None))
        self.assertEqual(self.visible(User.objects.create_superuser('root', password='x')), (200, both))

    def test_foreign_project_is_404(self):
        t = self.t
        for user in (t.pm2, t.lead2, t.devops2):
            self.client.force_login(user)
            self.assertEqual(self.client.get(f'/hub/projects/{t.project.pk}/').status_code, 404, user)
            self.assertEqual(self.client.post(f'/hub/projects/{t.project.pk}/status/',
                                              {'to_status': 'development'}).status_code, 404, user)

    def test_devops_loses_access_after_leaving(self):
        t = self.t
        membership = t.project.members.get(member=t.devops)
        services.remove_member(membership=membership, user=t.pm)
        self.client.force_login(t.devops)
        self.assertEqual(self.client.get(f'/hub/projects/{t.project.pk}/').status_code, 404)

    def card(self, user):
        self.client.force_login(user)
        resp = self.client.get(f'/hub/projects/{self.t.project.pk}/')
        self.assertEqual(resp.status_code, 200, user)
        return resp.content.decode()

    def test_card_blocks_by_role(self):
        t = self.t
        repo, note, contract_no = 'github.com/zea/ke-crm', 'сложный клиент', f'№ {t.contract.number}'
        head = self.card(t.head)
        for text in (repo, note, contract_no, 'Команда', 'История статусов', 'Изменить статус', 'Добавить участника'):
            self.assertIn(text, head)

        pm = self.card(t.pm)
        for text in (repo, note, 'Изменить статус', 'Добавить участника', 'Редактировать'):
            self.assertIn(text, pm)

        lead = self.card(t.lead)
        self.assertIn(repo, lead)
        self.assertIn('Добавить участника', lead)
        self.assertNotIn('Изменить статус', lead)
        self.assertNotIn('Редактировать', lead)

        bizdev = self.card(t.bizdev)
        self.assertIn(note, bizdev)
        self.assertNotIn(repo, bizdev)           # техинфо — только тем, кто в проекте
        for button in ('Изменить статус', 'Добавить участника', 'Редактировать'):
            self.assertNotIn(button, bizdev)

        mkt = self.card(t.marketing)
        for text in ('CRM для логистики', 'Kargo Express', 'CRM / внутренняя система', 'Планирование'):
            self.assertIn(text, mkt)
        for secret in (repo, note, contract_no, 'Команда', 'Hetzner', 'Пётр'):
            self.assertNotIn(secret, mkt)

        ops = self.card(t.devops)
        for text in (repo, 'Hetzner', 'Команда', 'Kargo Express'):
            self.assertIn(text, ops)
        self.assertNotIn(contract_no, ops)          # договоры DevOps не видит
        self.assertNotIn(f'/hub/partners/{t.company.pk}/', ops)
        self.assertNotIn('Изменить статус', ops)

    def test_marketing_list_limited_columns(self):
        self.client.force_login(self.t.marketing)
        html = self.client.get('/hub/projects/').content.decode()
        self.assertIn('Запуск', html)
        self.assertNotIn('Пётр', html)  # PM не показывается

    def test_action_permissions_via_http(self):
        t, pk = self.t, self.t.project.pk
        cases = {
            t.pm: {'edit': 200, 'status': 200, 'technical': 200, 'members/add': 200},
            t.lead: {'edit': 403, 'status': 403, 'technical': 200, 'members/add': 200},
            t.devops: {'edit': 403, 'status': 403, 'technical': 403, 'members/add': 403},
            t.bizdev: {'edit': 403, 'status': 403, 'technical': 403, 'members/add': 403},
            t.marketing: {'edit': 403, 'status': 403, 'technical': 403, 'members/add': 403},
            t.head: {'edit': 200, 'status': 200, 'technical': 200, 'members/add': 200},
        }
        for user, expected in cases.items():
            self.client.force_login(user)
            for action, code in expected.items():
                self.assertEqual(self.client.get(f'/hub/projects/{pk}/{action}/').status_code, code, (user, action))
        for user in (t.pm, t.lead, t.bizdev, t.marketing, t.devops, t.nobody):
            self.client.force_login(user)
            self.assertEqual(self.client.get('/hub/projects/add/').status_code, 403, user)

    def test_direct_posts_without_rights(self):
        t, pk = self.t, self.t.project.pk
        self.client.force_login(t.pm)
        # PM подменяет PM/тех. руководителя/договор в POST — поля не принимаются
        self.client.post(f'/hub/projects/{pk}/edit/', {
            'project_type': 'crm', 'priority': 'high', 'notes': 'ok',
            'pm': t.pm2.pk, 'technical_lead': t.lead2.pk, 'name': 'Взлом', 'code': 'HACK'})
        p = Project.objects.get(pk=pk)
        self.assertEqual((p.pm, p.technical_lead, p.name, p.priority), (t.pm, t.lead, 'CRM для логистики', 'high'))
        # PM не может отменить проект прямым POST
        self.assertEqual(self.client.post(f'/hub/projects/{pk}/status/',
                                          {'to_status': 'cancelled', 'comment': 'x'}).status_code, 403)
        # тех. руководитель не меняет статус, DevOps не добавляет участников
        self.client.force_login(t.lead)
        self.assertEqual(self.client.post(f'/hub/projects/{pk}/status/', {'to_status': 'development'}).status_code, 403)
        self.client.force_login(t.devops)
        self.assertEqual(self.client.post(f'/hub/projects/{pk}/members/add/', {
            'member': t.dev.pk, 'specialization': spec('Backend Developer').pk}).status_code, 403)
        self.assertEqual(Project.objects.get(pk=pk).status, P.PLANNING)

    def test_pause_via_form(self):
        self.client.force_login(self.t.pm)
        url = f'/hub/projects/{self.t.project.pk}/status/'
        resp = self.client.post(url, {'to_status': 'paused'})
        self.assertContains(resp, 'Укажите причину приостановки')
        self.client.post(url, {'to_status': 'paused', 'comment': 'Ждём контент'})
        resp = self.client.get(url)
        self.assertEqual([c[0] for c in resp.context['form'].fields['to_status'].choices], ['planning'])
        self.assertContains(resp, 'Возобновить — Планирование')

    def test_technical_form_has_no_secret_fields_and_rejects_secrets(self):
        self.client.force_login(self.t.lead)
        url = f'/hub/projects/{self.t.project.pk}/technical/'
        resp = self.client.get(url)
        fields = set(resp.context['form'].fields)
        self.assertEqual(fields, set(ProjectTechnicalInfo.TEXT_FIELDS))
        self.assertFalse({f for f in fields if any(w in f for w in ('password', 'secret', 'token', 'key'))})
        self.assertNotContains(resp, 'type="password"')
        self.assertContains(resp, 'Не храните здесь секреты')
        resp = self.client.post(url, {'server_info': 'db password=supersecret'})
        self.assertContains(resp, 'Похоже на секрет')
        self.assertNotIn('supersecret', ProjectTechnicalInfo.objects.get().server_info)

    def test_members_via_http(self):
        t, pk = self.t, self.t.project.pk
        self.client.force_login(t.lead)
        resp = self.client.get(f'/hub/projects/{pk}/members/add/')
        specs = {s.name for s in resp.context['form'].fields['specialization'].queryset}
        self.assertNotIn('UI/UX Designer', specs)
        self.assertIn('Backend Developer', specs)
        self.client.post(f'/hub/projects/{pk}/members/add/', {'member': t.dev.pk,
                                                              'specialization': spec('Backend Developer').pk})
        m = t.project.members.get(member=t.dev)
        self.assertContains(self.client.get(f'/hub/projects/{pk}/'), 'Дана')
        self.client.post(f'/hub/projects/{pk}/members/{m.pk}/remove/')
        m.refresh_from_db()
        self.assertFalse(m.is_active)


class ProjectListFilterTests(TestCase):
    def setUp(self):
        self.t = Team()
        services.change_project_status(project=self.t.other, to_status='development', user=self.t.head)
        late = make_project(self.t.head, self.t.contract, self.t.pm, self.t.lead, code='KE-WEB', name='Сайт',
                            project_type='website', priority='critical',
                            planned_end_date=date.today() - timedelta(days=3))
        self.late = late
        self.client.force_login(self.t.head)

    def codes(self, query):
        return [p.code for p in self.client.get('/hub/projects/' + query).context['projects']]

    def test_search_filters_sort(self):
        t = self.t
        self.assertEqual(self.codes('?q=бот'), ['KE-BOT'])
        self.assertEqual(len(self.codes('?q=kargo')), 3)  # поиск по компании
        self.assertEqual(set(self.codes('?status=development')), {'KE-BOT'})
        self.assertEqual(set(self.codes('?type=website')), {'KE-WEB'})
        self.assertEqual(set(self.codes(f'?pm={t.pm2.pk}')), {'KE-BOT'})
        self.assertEqual(set(self.codes(f'?lead={t.lead2.pk}')), {'KE-BOT'})
        self.assertEqual(set(self.codes('?priority=critical')), {'KE-WEB'})
        self.assertEqual(set(self.codes(f'?company={t.company.pk}')), {'KE-CRM', 'KE-BOT', 'KE-WEB'})
        self.assertEqual(set(self.codes('?status=overdue')), {'KE-WEB'})
        self.assertEqual(self.codes('?sort=priority')[0], 'KE-WEB')

    def test_pagination(self):
        for i in range(22):
            make_project(self.t.head, self.t.contract, self.t.pm, self.t.lead, code=f'P-{i:02d}')
        resp = self.client.get('/hub/projects/?sort=name')
        self.assertEqual(len(resp.context['projects']), 20)
        self.assertEqual(len(self.client.get('/hub/projects/?sort=name&page=2').context['projects']), 5)

    def test_dashboard(self):
        stats = self.client.get('/hub/').context['project_stats']
        self.assertEqual((stats['active'], stats['development'], stats['testing'], stats['support'], stats['overdue']),
                         (3, 1, 0, 0, 1))
        self.client.force_login(self.t.devops2)
        resp = self.client.get('/hub/')
        self.assertEqual(resp.context['project_stats']['active'], 0)  # у DevOps — только свои
        self.assertContains(resp, 'Проекты')

    def test_partner_card_projects_block(self):
        t = self.t
        resp = self.client.get(f'/hub/partners/{t.company.pk}/')
        self.assertContains(resp, 'Создать проект')
        self.assertContains(resp, 'KE-BOT')
        self.client.force_login(t.pm)
        resp = self.client.get(f'/hub/partners/{t.company.pk}/')
        self.assertContains(resp, 'KE-CRM')
        self.assertNotContains(resp, 'KE-BOT')      # чужой проект PM не видит
        self.assertNotContains(resp, 'Создать проект')

    def test_create_via_form(self):
        t = self.t
        form = self.client.get(f'/hub/projects/add/?company={t.company.pk}')
        self.assertEqual(form.context['form'].initial['contract'], t.contract.pk)
        pm_ids = {u.pk for u in form.context['form'].fields['pm'].queryset}
        self.assertEqual(pm_ids, {t.pm.pk, t.pm2.pk})
        resp = self.client.post('/hub/projects/add/', {
            'contract': t.contract.pk, 'name': 'Мобильное приложение', 'code': 'KE-APP',
            'project_type': 'mobile_app', 'priority': 'medium', 'pm': t.pm.pk, 'technical_lead': t.lead.pk})
        project = Project.objects.get(code='KE-APP')
        self.assertRedirects(resp, f'/hub/projects/{project.pk}/')
        resp = self.client.post('/hub/projects/add/', {
            'contract': t.contract.pk, 'name': 'x', 'code': 'KE-X', 'project_type': 'crm',
            'priority': 'medium', 'pm': t.lead.pk, 'technical_lead': t.lead.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('pm', resp.context['form'].errors)
