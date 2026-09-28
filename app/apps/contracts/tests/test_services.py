import os
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError

from apps.contracts import services
from apps.contracts.models import Contract, ContractDocument
from apps.partners import services as partner_services

from .utils import (
    C, DOCX, PDF, PrivateMediaTestCase, Role, S, activate, company_at_contract_stage, draft_contract,
    head, make_company, make_user, move_to, pdf, ready_terms, upload,
)


class ContractLifecycleTests(PrivateMediaTestCase):
    def setUp(self):
        self.head = head()
        self.bizdev = make_user('biz', Role.BIZDEV)
        self.company = company_at_contract_stage(self.head)

    def test_create_contract_as_draft_with_history(self):
        contract = draft_contract(self.company, self.bizdev)
        self.assertEqual((contract.status, contract.created_by), (C.DRAFT, self.bizdev))
        entry = contract.status_history.get()
        self.assertEqual((entry.from_status, entry.to_status), ('', C.DRAFT))

    def test_contract_only_for_approved_companies(self):
        new_company = make_company(self.head, name='Только пришла')
        with self.assertRaises(ValidationError):
            draft_contract(new_company, self.bizdev)

    def test_number_unique(self):
        draft_contract(self.company, self.bizdev)
        with self.assertRaises(ValidationError):
            draft_contract(self.company, self.bizdev)

    def test_share_percent_is_decimal_and_bounded(self):
        contract = ready_terms(draft_contract(self.company, self.bizdev), self.bizdev)
        contract.refresh_from_db()
        self.assertIsInstance(contract.share_percent, Decimal)
        self.assertEqual(contract.share_percent, Decimal('17.50'))
        for bad in (Decimal('0'), Decimal('100.01'), Decimal('-5')):
            contract.share_percent = bad
            with self.assertRaises(ValidationError, msg=bad):
                services.update_contract(contract=contract, user=self.bizdev)

    def test_other_base_requires_description(self):
        contract = draft_contract(self.company, self.bizdev)
        contract.calculation_base_type = 'other'
        contract.calculation_base_description = '  '
        with self.assertRaises(ValidationError) as ctx:
            services.update_contract(contract=contract, user=self.bizdev)
        self.assertIn('calculation_base_description', ctx.exception.error_dict)
        contract.calculation_base_description = '5% от продаж франшизы'
        services.update_contract(contract=contract, user=self.bizdev)

    def test_end_before_start_rejected(self):
        contract = draft_contract(self.company, self.bizdev, start_date=date(2026, 5, 1))
        contract.end_date = date(2026, 1, 1)
        with self.assertRaises(ValidationError):
            services.update_contract(contract=contract, user=self.bizdev)

    def test_full_lifecycle_and_history(self):
        contract = activate(draft_contract(self.company, self.bizdev), self.head)
        self.assertEqual(contract.status, C.ACTIVE)
        chain = list(contract.status_history.order_by('changed_at', 'id').values_list('to_status', flat=True))
        self.assertEqual(chain, [C.DRAFT, C.REVIEW, C.READY, C.ACTIVE])

    def test_invalid_transitions(self):
        contract = draft_contract(self.company, self.head)
        for target in (C.ACTIVE, C.READY, C.EXPIRED, C.TERMINATED, 'bogus'):
            with self.assertRaises((ValidationError, PermissionDenied), msg=target):
                services.change_contract_status(contract=contract, to_status=target, user=self.head)
        contract.refresh_from_db()
        self.assertEqual(contract.status, C.DRAFT)

    def test_ready_requires_terms(self):
        contract = draft_contract(self.company, self.bizdev)
        services.change_contract_status(contract=contract, to_status=C.REVIEW, user=self.bizdev)
        with self.assertRaises(ValidationError) as ctx:
            services.change_contract_status(contract=contract, to_status=C.READY, user=self.bizdev)
        self.assertIn('процент', str(ctx.exception))

    def test_activation_only_by_head(self):
        contract = draft_contract(self.company, self.bizdev)
        ready_terms(contract, self.bizdev)
        services.upload_contract_file(contract=contract, uploaded=pdf(), user=self.bizdev)
        services.change_contract_status(contract=contract, to_status=C.REVIEW, user=self.bizdev)
        services.change_contract_status(contract=contract, to_status=C.READY, user=self.bizdev)
        with self.assertRaises(PermissionDenied):
            services.change_contract_status(contract=contract, to_status=C.ACTIVE, user=self.bizdev)
        self.assertNotIn(C.ACTIVE, services.allowed_transitions(contract, self.bizdev))
        self.assertIn(C.ACTIVE, services.allowed_transitions(contract, self.head))
        services.change_contract_status(contract=contract, to_status=C.ACTIVE, user=self.head)

    def test_activation_requires_signed_file(self):
        contract = draft_contract(self.company, self.head)
        with self.assertRaises(ValidationError) as ctx:
            activate(contract, self.head, with_file=False)
        self.assertIn('файл', str(ctx.exception))

    def test_activation_requires_company_at_contract_stage(self):
        company = move_to(make_company(self.head, name='Переговоры'), S.NEGOTIATION, self.head)
        contract = draft_contract(company, self.head, number='N-1')
        with self.assertRaises(ValidationError) as ctx:
            activate(contract, self.head)
        self.assertIn('«Договор»', str(ctx.exception))

    def test_terminate_only_head_with_reason(self):
        contract = activate(draft_contract(self.company, self.head), self.head)
        with self.assertRaises(PermissionDenied):
            services.change_contract_status(contract=contract, to_status=C.TERMINATED,
                                            user=self.bizdev, comment='x')
        with self.assertRaises(ValidationError):
            services.change_contract_status(contract=contract, to_status=C.TERMINATED, user=self.head)
        services.change_contract_status(contract=contract, to_status=C.TERMINATED, user=self.head,
                                        comment='Партнёр прекратил деятельность')
        self.assertEqual(services.allowed_transitions(contract, self.head), ())

    def test_expired_only_after_end_date(self):
        contract = activate(draft_contract(self.company, self.head), self.head)
        with self.assertRaises(ValidationError):
            services.change_contract_status(contract=contract, to_status=C.EXPIRED, user=self.bizdev)
        Contract.objects.filter(pk=contract.pk).update(end_date=date.today() - timedelta(days=1))
        contract.refresh_from_db()
        services.change_contract_status(contract=contract, to_status=C.EXPIRED, user=self.bizdev)

    def test_signed_contract_is_locked(self):
        contract = activate(draft_contract(self.company, self.head), self.head)
        contract.share_percent = Decimal('50')
        with self.assertRaises(ValidationError):
            services.update_contract(contract=contract, user=self.head)
        with self.assertRaises(ValidationError):
            services.upload_contract_file(contract=contract, uploaded=pdf(), user=self.head)
        contract.refresh_from_db()
        self.assertEqual(contract.share_percent, Decimal('17.50'))

    def test_financial_fields_protected_in_service(self):
        """Пользователь без view_financial_terms не меняет процент даже в обход формы."""
        contract = draft_contract(self.company, self.head)
        tech = make_user('tech', Role.TECH_LEAD)
        contract.share_percent = Decimal('99')
        with self.assertRaises(PermissionDenied):
            services.update_contract(contract=contract, user=tech)
        contract.refresh_from_db()
        self.assertIsNone(contract.share_percent)

    def test_status_change_requires_manage(self):
        contract = draft_contract(self.company, self.head)
        with self.assertRaises(PermissionDenied):
            services.change_contract_status(contract=contract, to_status=C.REVIEW,
                                            user=make_user('pm', Role.PM))


class MultipleContractsTests(PrivateMediaTestCase):
    def setUp(self):
        self.head = head()
        self.company = company_at_contract_stage(self.head)

    def test_several_contracts_one_active(self):
        first = activate(draft_contract(self.company, self.head, number='2026-1'), self.head)
        second = draft_contract(self.company, self.head, number='2027-1')
        with self.assertRaises(ValidationError) as ctx:
            activate(second, self.head)
        self.assertIn('2026-1', str(ctx.exception))
        services.change_contract_status(contract=first, to_status=C.TERMINATED, user=self.head,
                                        comment='Заменён новым договором')
        second.refresh_from_db()
        services.change_contract_status(contract=second, to_status=C.ACTIVE, user=self.head)
        self.assertEqual(self.company.contracts.count(), 2)
        self.assertEqual(self.company.contracts.filter(status=C.ACTIVE).get(), second)

    def test_db_constraint_blocks_second_active(self):
        from django.db import IntegrityError, transaction
        activate(draft_contract(self.company, self.head, number='A'), self.head)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Contract.objects.create(company=self.company, number='B', title='x', status=C.ACTIVE)


class CompanyPartnerTransitionTests(PrivateMediaTestCase):
    def setUp(self):
        self.head = head()
        self.company = company_at_contract_stage(self.head)

    def test_partner_requires_active_contract(self):
        with self.assertRaises(ValidationError):
            partner_services.make_partner(company=self.company, user=self.head)
        contract = draft_contract(self.company, self.head)
        with self.assertRaises(ValidationError):
            partner_services.change_status(company=self.company, to_status=S.PARTNER, user=self.head)
        activate(contract, self.head)
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.CONTRACT)  # автоматически НЕ становится партнёром
        partner_services.make_partner(company=self.company, user=self.head)
        self.company.refresh_from_db()
        self.assertEqual(self.company.status, S.PARTNER)

    def test_partner_not_in_manual_status_form(self):
        activate(draft_contract(self.company, self.head), self.head)
        self.assertNotIn(S.PARTNER, partner_services.allowed_transitions(self.company))

    def test_make_partner_only_from_contract_stage(self):
        company = make_company(self.head, name='Новая')
        with self.assertRaises(ValidationError):
            partner_services.make_partner(company=company, user=self.head)


class FileTests(PrivateMediaTestCase):
    def setUp(self):
        self.head = head()
        self.contract = draft_contract(company_at_contract_stage(self.head), self.head)

    def test_pdf_stored_privately_under_uuid(self):
        services.upload_contract_file(contract=self.contract, uploaded=pdf('../../etc/Договор №1.pdf'),
                                      user=self.head)
        name = self.contract.file.name
        self.assertTrue(name.startswith('contracts/main/'))
        self.assertNotIn('Договор', name)
        self.assertRegex(os.path.basename(name), r'^[0-9a-f]{32}\.pdf$')
        self.assertTrue(os.path.exists(os.path.join(settings.PRIVATE_MEDIA_ROOT, name)))
        self.assertFalse(os.path.exists(os.path.join(settings.MEDIA_ROOT, name)))
        self.assertEqual(self.contract.file_original_name, 'Договор_1.pdf')
        with self.assertRaises(NotImplementedError):
            self.contract.file.url  # у приватного файла нет URL

    def test_rejected_extensions_and_content(self):
        cases = [
            upload('contract.exe', b'MZ\x90\x00'),
            upload('contract.html', b'<script>alert(1)</script>'),
            upload('contract.pdf.exe', PDF),
            upload('contract.docx', DOCX),               # основной договор — только PDF
            upload('fake.pdf', b'<html>not a pdf</html>'),  # расширение не соответствует содержимому
            upload('empty.pdf', b''),
        ]
        for uploaded in cases:
            with self.assertRaises(ValidationError, msg=uploaded.name):
                services.upload_contract_file(contract=self.contract, uploaded=uploaded, user=self.head)
        self.contract.refresh_from_db()
        self.assertFalse(self.contract.file)

    def test_size_limit(self):
        with mock.patch.object(services, 'MAX_UPLOAD_SIZE', 10):
            with self.assertRaises(ValidationError):
                services.upload_contract_file(contract=self.contract, uploaded=pdf(), user=self.head)

    def test_replace_deletes_old_file(self):
        services.upload_contract_file(contract=self.contract, uploaded=pdf('v1.pdf'), user=self.head)
        old_path = self.contract.file.path
        with self.captureOnCommitCallbacks(execute=True):
            services.upload_contract_file(contract=self.contract, uploaded=pdf('v2.pdf'), user=self.head)
        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(self.contract.file.path))

    def test_add_documents(self):
        doc = services.add_document(
            document=ContractDocument(contract=self.contract, document_type='spec', title='ТЗ на CRM'),
            uploaded=upload('ТЗ.docx', DOCX), user=self.head)
        self.assertEqual((doc.original_name, doc.size, doc.uploaded_by), ('ТЗ.docx', len(DOCX), self.head))
        self.assertFalse(doc.is_financial)
        act = services.add_document(
            document=ContractDocument(contract=self.contract, document_type='act', title='Акт'),
            uploaded=upload('act.pdf', PDF), user=self.head)
        self.assertTrue(act.is_financial)
        for bad in (upload('x.svg', b'<svg onload=alert(1)>'), upload('x.html', b'<html>')):
            with self.assertRaises(ValidationError):
                services.add_document(document=ContractDocument(contract=self.contract,
                                      document_type='other', title='x'), uploaded=bad, user=self.head)
        self.assertEqual(self.contract.documents.count(), 2)
