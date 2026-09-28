from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.partners import services
from apps.partners.models import (
    CandidateAssessment, CandidateDecision, Company, CompanyContact, CompanyStatusHistory,
)

from .utils import S, head, make_company, move_to


class CompanyServiceTests(TestCase):
    def setUp(self):
        self.user = head()

    def test_create_company_starts_as_new_with_history(self):
        company = make_company(self.user, industry='Ритейл', company_type='startup')
        self.assertEqual(company.status, S.NEW)
        self.assertEqual(company.created_by, self.user)
        entry = company.status_history.get()
        self.assertEqual((entry.from_status, entry.to_status, entry.changed_by),
                         ('', S.NEW, self.user))

    def test_create_ignores_status_passed_from_outside(self):
        company = services.create_company(company=Company(name='X', status=S.PARTNER), user=self.user)
        self.assertEqual(company.status, S.NEW)

    def test_update_company_keeps_status(self):
        company = move_to(make_company(self.user), S.ANALYSIS, self.user)
        company.name = 'Альфа Групп'
        services.update_company(company=company, user=self.user)
        company.refresh_from_db()
        self.assertEqual((company.name, company.status), ('Альфа Групп', S.ANALYSIS))

    def test_name_is_required(self):
        with self.assertRaises(ValidationError):
            services.create_company(company=Company(name=''), user=self.user)


class StatusTransitionTests(TestCase):
    def setUp(self):
        self.user = head()
        self.company = make_company(self.user)

    def test_change_status_writes_history(self):
        before = self.company.status_changed_at
        record = services.change_status(company=self.company, to_status=S.ANALYSIS,
                                        user=self.user, comment='Начали изучать')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.ANALYSIS)
        self.assertGreaterEqual(self.company.status_changed_at, before)
        self.assertEqual((record.from_status, record.to_status, record.comment, record.changed_by),
                         (S.NEW, S.ANALYSIS, 'Начали изучать', self.user))
        self.assertEqual(self.company.status_history.count(), 2)

    def test_invalid_transition_rejected(self):
        for target in (S.PARTNER, S.CONTRACT, S.DISCUSSION, 'nonsense'):
            with self.assertRaises(ValidationError, msg=target):
                services.change_status(company=self.company, to_status=target, user=self.user)
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.NEW)
        self.assertEqual(self.company.status_history.count(), 1)

    def test_approved_only_by_decision(self):
        move_to(self.company, S.DISCUSSION, self.user)
        with self.assertRaises(ValidationError):
            services.change_status(company=self.company, to_status=S.APPROVED, user=self.user)
        self.assertNotIn(S.APPROVED, services.allowed_transitions(self.company))

    def test_rejection_requires_reason(self):
        for comment in ('', '   '):
            with self.assertRaises(ValidationError):
                services.change_status(company=self.company, to_status=S.REJECTED,
                                       user=self.user, comment=comment)
        services.change_status(company=self.company, to_status=S.REJECTED,
                               user=self.user, comment='Не наш профиль')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.REJECTED)
        self.assertEqual(self.company.status_history.first().comment, 'Не наш профиль')

    def test_rejected_company_is_kept_and_can_return(self):
        services.change_status(company=self.company, to_status=S.REJECTED, user=self.user, comment='Нет')
        self.assertTrue(Company.objects.filter(pk=self.company.pk).exists())
        self.assertEqual(services.allowed_transitions(self.company), (S.NEW,))
        services.change_status(company=self.company, to_status=S.NEW, user=self.user, comment='Вернули')
        self.assertEqual(self.company.status_history.count(), 3)

    def test_full_path_to_partner(self):
        move_to(self.company, S.PARTNER, self.user)
        self.assertEqual(self.company.status, S.PARTNER)
        chain = list(self.company.status_history.order_by('changed_at', 'id')
                     .values_list('to_status', flat=True))
        self.assertEqual(chain, [S.NEW, S.ANALYSIS, S.DISCUSSION, S.APPROVED,
                                 S.NEGOTIATION, S.CONTRACT, S.PARTNER])
        self.assertEqual(services.allowed_transitions(self.company), ())

    def test_step_back_allowed(self):
        move_to(self.company, S.NEGOTIATION, self.user)
        # уже одобренного кандидата можно вернуть из переговоров вручную
        self.assertIn(S.APPROVED, services.allowed_transitions(self.company))
        services.change_status(company=self.company, to_status=S.APPROVED, user=self.user)
        self.assertEqual(self.company.status, S.APPROVED)


class DecisionTests(TestCase):
    def setUp(self):
        self.user = head()
        self.company = move_to(make_company(self.user), S.DISCUSSION, self.user)

    def test_approve_sets_approved_not_partner(self):
        decision = services.make_decision(company=self.company, decision='approve',
                                          user=self.user, comment='Берём')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.APPROVED)
        self.assertEqual(decision.created_by, self.user)
        self.assertIn('Одобрить', self.company.status_history.first().comment)

    def test_approve_only_after_discussion(self):
        company = move_to(make_company(self.user, name='Бета'), S.ANALYSIS, self.user)
        with self.assertRaises(ValidationError):
            services.make_decision(company=company, decision='approve', user=self.user)
        self.assertFalse(CandidateDecision.objects.filter(company=company).exists())

    def test_reject_requires_comment_and_rejects(self):
        with self.assertRaises(ValidationError):
            services.make_decision(company=self.company, decision='reject', user=self.user)
        self.assertFalse(self.company.decisions.exists())
        services.make_decision(company=self.company, decision='reject', user=self.user,
                               comment='Финансы непрозрачны')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.REJECTED)

    def test_rework_returns_to_analysis(self):
        services.make_decision(company=self.company, decision='rework', user=self.user, comment='Нужны цифры')
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.ANALYSIS)
        # На стадии «Анализ» «на доработку» не меняет статус
        services.make_decision(company=self.company, decision='rework', user=self.user)
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.ANALYSIS)
        self.assertEqual(self.company.decisions.count(), 2)

    def test_no_decision_outside_review_stages(self):
        company = make_company(self.user, name='Гамма')
        for decision in ('approve', 'rework', 'reject'):
            with self.assertRaises(ValidationError):
                services.make_decision(company=company, decision=decision, user=self.user, comment='x')


class ContactAndAssessmentTests(TestCase):
    def setUp(self):
        self.user = head()
        self.company = make_company(self.user)

    def test_several_contacts_single_primary(self):
        first = services.save_contact(contact=CompanyContact(company=self.company, name='Айбек', is_primary=True))
        second = services.save_contact(contact=CompanyContact(company=self.company, name='Мира', is_primary=True))
        services.save_contact(contact=CompanyContact(company=self.company, name='Бакыт'))
        first.refresh_from_db()
        self.assertEqual(self.company.contacts.count(), 3)
        self.assertFalse(first.is_primary)
        self.assertEqual(self.company.contacts.get(is_primary=True), second)

    def test_assessment_create_and_update(self):
        assessment = services.save_assessment(
            assessment=CandidateAssessment(company=self.company, revenue='≈ 1 млн сом/мес', mvp_state='yes'),
            user=self.user,
        )
        self.assertEqual(assessment.created_by, self.user)
        assessment.risks_for_zea = 'Зависимость от одного клиента'
        other = head('head2')
        services.save_assessment(assessment=assessment, user=other)
        assessment.refresh_from_db()
        self.assertEqual((assessment.created_by, assessment.updated_by), (self.user, other))
        self.assertEqual(CandidateAssessment.objects.count(), 1)
