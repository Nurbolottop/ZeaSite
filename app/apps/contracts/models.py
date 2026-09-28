"""Договоры партнёрства ZEA.

Статус меняется только через services.change_contract_status().
Файлы — только в private_storage (вне MEDIA_ROOT, без публичного URL),
отдаются через views с проверкой прав. Физическое имя файла — UUID.
"""
import os
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.hub.models import AuthoredModel
from apps.hub.storage import private_storage
from apps.partners.models import Company


def _uuid_path(prefix, filename):
    """Физическое имя — UUID; от пользовательского имени берётся только
    расширение (уже проверенное в services.validate_upload)."""
    ext = os.path.splitext(filename)[1].lower()
    return f'{prefix}/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}'


def contract_file_path(instance, filename):
    return _uuid_path('contracts/main', filename)


def contract_document_path(instance, filename):
    return _uuid_path('contracts/documents', filename)


class ContractStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    REVIEW = 'review', 'На согласовании'
    READY = 'ready', 'Готов к подписанию'
    ACTIVE = 'active', 'Действует'
    EXPIRED = 'expired', 'Истёк'
    TERMINATED = 'terminated', 'Расторгнут'


class CalculationBase(models.TextChoices):
    TOTAL_REVENUE = 'total_revenue', 'Общая выручка компании'
    PRODUCT_REVENUE = 'product_revenue', 'Выручка продукта / направления'
    SYSTEM_REVENUE = 'system_revenue', 'Продажи через созданную ZEA систему'
    PROFIT = 'profit', 'Прибыль'
    OTHER = 'other', 'Другая договорная база'


# Поля с финансовыми условиями — видны только при contracts.view_financial_terms
FINANCIAL_FIELDS = ('share_percent', 'calculation_base_type', 'calculation_base_description',
                    'payment_terms')


class Contract(AuthoredModel):
    company = models.ForeignKey(Company, verbose_name='Компания', on_delete=models.PROTECT,
                                related_name='contracts')
    number = models.CharField('Номер договора', max_length=64)
    title = models.CharField('Название', max_length=255)
    status = models.CharField('Статус', max_length=20, choices=ContractStatus.choices,
                              default=ContractStatus.DRAFT, editable=False, db_index=True)
    status_changed_at = models.DateTimeField('Статус изменён', default=timezone.now, editable=False)

    start_date = models.DateField('Дата начала', null=True, blank=True)
    end_date = models.DateField('Дата окончания', null=True, blank=True,
                                help_text='Пусто — бессрочный')
    signed_date = models.DateField('Дата подписания', null=True, blank=True)
    description = models.TextField('Описание', blank=True)

    # ── Финансовые условия (скрываются без contracts.view_financial_terms) ──
    share_percent = models.DecimalField(
        'Процент ZEA', max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100'))],
    )
    calculation_base_type = models.CharField('База расчёта', max_length=30,
                                             choices=CalculationBase.choices, blank=True)
    calculation_base_description = models.TextField(
        'База расчёта — точная формулировка', blank=True,
        help_text='От чего именно ZEA получает процент, как в договоре. Обязательно для «Другая».',
    )
    payment_terms = models.TextField('Условия оплаты', blank=True)

    # ── Остальные условия ──
    zea_obligations = models.TextField('Обязанности ZEA', blank=True)
    partner_obligations = models.TextField('Обязанности партнёра', blank=True)
    termination_terms = models.TextField('Условия прекращения', blank=True)
    additional_terms = models.TextField('Дополнительные условия', blank=True)

    # ── Подписанный договор ──
    file = models.FileField('Файл договора (PDF)', storage=private_storage,
                            upload_to=contract_file_path, blank=True, max_length=255)
    file_original_name = models.CharField('Имя файла', max_length=255, blank=True, editable=False)
    file_uploaded_at = models.DateTimeField('Файл загружен', null=True, blank=True, editable=False)

    class Meta:
        verbose_name = 'Договор'
        verbose_name_plural = 'Договоры'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(fields=['number'], name='contracts_unique_number'),
            # Не больше одного действующего договора партнёрства у компании
            models.UniqueConstraint(fields=['company'], condition=Q(status='active'),
                                    name='contracts_one_active_per_company'),
        ]

    def __str__(self):
        return f'№ {self.number} — {self.company}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('contracts:detail', args=[self.pk])


class ContractStatusHistory(models.Model):
    contract = models.ForeignKey(Contract, verbose_name='Договор', on_delete=models.CASCADE,
                                 related_name='status_history')
    from_status = models.CharField('Из статуса', max_length=20, choices=ContractStatus.choices,
                                   blank=True)
    to_status = models.CharField('В статус', max_length=20, choices=ContractStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Изменил', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    changed_at = models.DateTimeField('Дата', default=timezone.now)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Изменение статуса договора'
        verbose_name_plural = 'История статусов договоров'
        ordering = ('-changed_at', '-id')

    def __str__(self):
        return f'{self.contract}: {self.get_from_status_display() or "—"} → {self.get_to_status_display()}'


class DocumentType(models.TextChoices):
    APPENDIX = 'appendix', 'Приложение к договору'
    SUPPLEMENT = 'supplement', 'Дополнительное соглашение'
    SPEC = 'spec', 'Техническое задание'
    ACT = 'act', 'Акт'
    OTHER = 'other', 'Другой документ'


# Документы, которые видят роли без доступа к финансовым условиям.
# ТЗ нужно PM и техническому руководителю; приложения, допсоглашения
# и акты могут содержать проценты и суммы.
NON_FINANCIAL_DOCUMENT_TYPES = {DocumentType.SPEC}


class ContractDocument(models.Model):
    # Публичный идентификатор для URL скачивания — не подбирается перебором
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    contract = models.ForeignKey(Contract, verbose_name='Договор', on_delete=models.CASCADE,
                                 related_name='documents')
    document_type = models.CharField('Тип', max_length=20, choices=DocumentType.choices)
    title = models.CharField('Название', max_length=255)
    file = models.FileField('Файл', storage=private_storage, upload_to=contract_document_path,
                            max_length=255)
    original_name = models.CharField('Имя файла', max_length=255, editable=False)
    size = models.PositiveIntegerField('Размер, байт', default=0, editable=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Загрузил', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+', editable=False)
    uploaded_at = models.DateTimeField('Загружен', default=timezone.now, editable=False)
    note = models.TextField('Заметка', blank=True)

    class Meta:
        verbose_name = 'Документ договора'
        verbose_name_plural = 'Документы договоров'
        ordering = ('-uploaded_at',)

    def __str__(self):
        return f'{self.get_document_type_display()}: {self.title}'

    @property
    def is_financial(self):
        return self.document_type not in NON_FINANCIAL_DOCUMENT_TYPES
