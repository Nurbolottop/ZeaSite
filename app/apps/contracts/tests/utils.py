import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.contracts import services
from apps.contracts.models import Contract, ContractStatus
from apps.partners.tests.utils import S, head, make_company, make_user, move_to  # noqa: F401
from apps.users.roles import Role  # noqa: F401

C = ContractStatus
PDF = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'
DOCX = b'PK\x03\x04' + b'\x00' * 40


def pdf(name='Договор подписан.pdf', content=PDF):
    return SimpleUploadedFile(name, content, content_type='application/pdf')


def upload(name, content, content_type='application/octet-stream'):
    return SimpleUploadedFile(name, content, content_type=content_type)


class PrivateMediaTestCase(TestCase):
    """Файлы тестов — во временной приватной папке, реальная не трогается."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._private_root = tempfile.mkdtemp(prefix='zea-private-')
        cls._media_root = tempfile.mkdtemp(prefix='zea-media-')
        cls._override = override_settings(PRIVATE_MEDIA_ROOT=cls._private_root,
                                          MEDIA_ROOT=cls._media_root)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._private_root, ignore_errors=True)
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()


def company_at_contract_stage(user, name='Партнёр-кандидат'):
    return move_to(make_company(user, name=name), S.CONTRACT, user)


def draft_contract(company, user, number='ZEA-001', **extra):
    fields = dict(company=company, number=number, title='Договор технологического партнёрства')
    fields.update(extra)
    return services.create_contract(contract=Contract(**fields), user=user)


def ready_terms(contract, user):
    contract.share_percent = Decimal('17.50')
    contract.calculation_base_type = 'system_revenue'
    contract.calculation_base_description = 'Продажи через CRM, созданную ZEA'
    contract.start_date = date(2026, 10, 1)
    contract.signed_date = date(2026, 9, 28)
    services.update_contract(contract=contract, user=user)
    return contract


def activate(contract, user, with_file=True):
    """Черновик → Готов → Действует (полный процесс через сервисы)."""
    ready_terms(contract, user)
    if with_file:
        services.upload_contract_file(contract=contract, uploaded=pdf(), user=user)
    services.change_contract_status(contract=contract, to_status=C.REVIEW, user=user)
    services.change_contract_status(contract=contract, to_status=C.READY, user=user)
    services.change_contract_status(contract=contract, to_status=C.ACTIVE, user=user)
    contract.refresh_from_db()
    return contract
