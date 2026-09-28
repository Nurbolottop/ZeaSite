"""Бизнес-логика договоров. Views вызывают только эти функции.

Права, критичные для денег (активация, расторжение, финансовые поля),
проверяются здесь, а не только во view — прямой POST их не обойдёт.
"""
import os

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import get_valid_filename

from apps.partners.models import CompanyStatus
from apps.users.access import has_permission

from .models import (
    FINANCIAL_FIELDS, CalculationBase, Contract, ContractDocument, ContractStatus,
    ContractStatusHistory,
)

C = ContractStatus
CS = CompanyStatus

TRANSITIONS = {
    C.DRAFT:      (C.REVIEW,),
    C.REVIEW:     (C.DRAFT, C.READY),
    C.READY:      (C.REVIEW, C.ACTIVE),
    C.ACTIVE:     (C.EXPIRED, C.TERMINATED),
    C.EXPIRED:    (),
    C.TERMINATED: (),
}

# Переходы, доступные только с правом contracts.activate (Руководитель)
ACTIVATE_ONLY = {C.ACTIVE, C.TERMINATED}

# Условия договора можно менять только до подписания
EDITABLE_STATUSES = {C.DRAFT, C.REVIEW, C.READY}

# На каких стадиях компании можно готовить договор
COMPANY_STATUSES_FOR_CONTRACT = {CS.APPROVED, CS.NEGOTIATION, CS.CONTRACT, CS.PARTNER}
# Действующим договор становится, когда компания на стадии «Договор» (или уже партнёр)
COMPANY_STATUSES_FOR_ACTIVATION = {CS.CONTRACT, CS.PARTNER}

# ── Файлы ─────────────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 МБ

# расширение → (MIME для скачивания, допустимые сигнатуры начала файла)
FILE_TYPES = {
    '.pdf':  ('application/pdf', (b'%PDF-',)),
    '.docx': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', (b'PK\x03\x04',)),
    '.xlsx': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', (b'PK\x03\x04',)),
    '.doc':  ('application/msword', (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',)),
    '.xls':  ('application/vnd.ms-excel', (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',)),
    '.png':  ('image/png', (b'\x89PNG\r\n\x1a\n',)),
    '.jpg':  ('image/jpeg', (b'\xff\xd8\xff',)),
    '.jpeg': ('image/jpeg', (b'\xff\xd8\xff',)),
}
CONTRACT_FILE_EXTENSIONS = ('.pdf',)
DOCUMENT_EXTENSIONS = tuple(FILE_TYPES)


def validate_upload(uploaded, allowed_extensions, field='file'):
    """Проверка размера, расширения и содержимого (сигнатуры) файла.

    Имени от пользователя не доверяем: оно используется только как подпись
    при скачивании (после очистки), физическое имя — UUID.
    """
    if uploaded is None:
        raise ValidationError({field: 'Выберите файл.'})
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in allowed_extensions:
        allowed = ', '.join(e.lstrip('.').upper() for e in allowed_extensions)
        raise ValidationError({field: f'Недопустимый тип файла. Разрешено: {allowed}.'})
    if uploaded.size > MAX_UPLOAD_SIZE:
        raise ValidationError({field: f'Файл больше {MAX_UPLOAD_SIZE // (1024 * 1024)} МБ.'})
    if uploaded.size == 0:
        raise ValidationError({field: 'Файл пустой.'})
    head = uploaded.read(16)
    uploaded.seek(0)
    if not any(head.startswith(sig) for sig in FILE_TYPES[ext][1]):
        raise ValidationError({field: 'Содержимое файла не соответствует расширению.'})
    return ext


def safe_display_name(name):
    base = os.path.basename(name or '')
    return (get_valid_filename(base) or 'file')[:255]


def content_type_for(name):
    return FILE_TYPES.get(os.path.splitext(name)[1].lower(), ('application/octet-stream',))[0]


def _delete_file_later(storage, name):
    if name:
        transaction.on_commit(lambda: storage.delete(name))


# ── Договор ───────────────────────────────────────────────────────────────

def _log(contract, from_status, to_status, user, comment, at):
    return ContractStatusHistory.objects.create(
        contract=contract, from_status=from_status, to_status=to_status,
        changed_by=user, changed_at=at, comment=comment,
    )


def _check_financial_access(contract, user):
    """Без contracts.view_financial_terms финансовые поля менять нельзя (даже POST в обход формы)."""
    if has_permission(user, 'contracts.view_financial_terms'):
        return
    if contract.pk is None:
        changed = [f for f in FINANCIAL_FIELDS if getattr(contract, f) not in (None, '')]
    else:
        current = Contract.objects.filter(pk=contract.pk).values(*FINANCIAL_FIELDS).get()
        changed = [f for f in FINANCIAL_FIELDS if getattr(contract, f) != current[f]]
    if changed:
        raise PermissionDenied('Нет права изменять финансовые условия договора.')


def _clean_terms(contract):
    contract.full_clean()
    errors = {}
    if contract.calculation_base_type == CalculationBase.OTHER and not contract.calculation_base_description.strip():
        errors['calculation_base_description'] = 'Для «Другая договорная база» опишите базу расчёта.'
    if contract.start_date and contract.end_date and contract.end_date < contract.start_date:
        errors['end_date'] = 'Дата окончания раньше даты начала.'
    if errors:
        raise ValidationError(errors)


@transaction.atomic
def create_contract(*, contract: Contract, user) -> Contract:
    if contract.company.status not in COMPANY_STATUSES_FOR_CONTRACT:
        raise ValidationError({'company': (
            'Договор готовится для одобренных компаний (стадии «Одобрен», «Переговоры», '
            '«Договор») или действующих партнёров.'
        )})
    _check_financial_access(contract, user)
    now = timezone.now()
    contract.status = C.DRAFT
    contract.status_changed_at = now
    contract.created_by = user
    contract.updated_by = user
    _clean_terms(contract)
    contract.save()
    _log(contract, '', C.DRAFT, user, 'Договор создан', now)
    return contract


def update_contract(*, contract: Contract, user) -> Contract:
    current_status = Contract.objects.values_list('status', flat=True).get(pk=contract.pk)
    if current_status not in EDITABLE_STATUSES:
        raise ValidationError('Подписанный договор не редактируется. Изменения оформляются '
                              'дополнительным соглашением (раздел «Документы»).')
    _check_financial_access(contract, user)
    contract.status = current_status  # статус меняется только change_contract_status
    contract.updated_by = user
    _clean_terms(contract)
    contract.save()
    return contract


def readiness_errors(contract, to_status):
    """Чего не хватает договору для перехода в «Готов» / «Действует»."""
    missing = []
    if to_status in (C.READY, C.ACTIVE):
        if contract.share_percent is None:
            missing.append('процент ZEA')
        if not contract.calculation_base_type:
            missing.append('база расчёта')
        if not contract.start_date:
            missing.append('дата начала')
    if to_status == C.ACTIVE:
        if not contract.signed_date:
            missing.append('дата подписания')
        if not contract.file:
            missing.append('файл подписанного договора')
    return missing


def allowed_transitions(contract, user):
    if not has_permission(user, 'contracts.manage'):
        return ()
    return tuple(t for t in TRANSITIONS.get(contract.status, ())
                 if t not in ACTIVATE_ONLY or has_permission(user, 'contracts.activate'))


@transaction.atomic
def change_contract_status(*, contract: Contract, to_status: str, user,
                           comment: str = '') -> ContractStatusHistory:
    """Единственная точка смены статуса договора."""
    comment = (comment or '').strip()
    if not has_permission(user, 'contracts.manage'):
        raise PermissionDenied('Нет права изменять договоры.')
    if to_status in ACTIVATE_ONLY and not has_permission(user, 'contracts.activate'):
        raise PermissionDenied('Активировать и расторгать договор может только Руководитель.')

    locked = Contract.objects.select_for_update().select_related('company').get(pk=contract.pk)
    from_status = locked.status
    if to_status not in C.values:
        raise ValidationError({'to_status': 'Неизвестный статус.'})
    if to_status not in TRANSITIONS.get(from_status, ()):
        raise ValidationError({'to_status': (
            f'Нельзя перевести договор из «{C(from_status).label}» в «{C(to_status).label}».'
        )})

    missing = readiness_errors(locked, to_status)
    if missing:
        raise ValidationError({'to_status': f'Не заполнено: {", ".join(missing)}.'})

    if to_status == C.ACTIVE:
        if locked.company.status not in COMPANY_STATUSES_FOR_ACTIVATION:
            raise ValidationError({'to_status': (
                'Сначала переведите компанию на стадию «Договор» '
                f'(сейчас — «{locked.company.get_status_display()}»).'
            )})
        # Блокируем договоры компании: два действующих одновременно быть не может
        others = (Contract.objects.select_for_update()
                  .filter(company_id=locked.company_id, status=C.ACTIVE).exclude(pk=locked.pk))
        if others.exists():
            raise ValidationError({'to_status': (
                f'У компании уже есть действующий договор № {others.first().number}. '
                'Сначала переведите его в «Истёк» или «Расторгнут».'
            )})
    if to_status == C.TERMINATED and not comment:
        raise ValidationError({'comment': 'Укажите причину расторжения.'})
    if to_status == C.EXPIRED and (not locked.end_date or locked.end_date > timezone.localdate()):
        raise ValidationError({'to_status': 'Договор можно отметить истёкшим только после даты окончания.'})

    now = timezone.now()
    locked.status = to_status
    locked.status_changed_at = now
    locked.updated_by = user
    locked.save(update_fields=['status', 'status_changed_at', 'updated_by', 'updated_at'])
    contract.status = locked.status
    contract.status_changed_at = now
    return _log(contract, from_status, to_status, user, comment, now)


@transaction.atomic
def upload_contract_file(*, contract: Contract, uploaded, user) -> Contract:
    """Загрузка/замена подписанного договора (только PDF, только до подписания)."""
    if contract.status not in EDITABLE_STATUSES:
        raise ValidationError('Файл действующего или закрытого договора заменить нельзя.')
    validate_upload(uploaded, CONTRACT_FILE_EXTENSIONS)
    old_name = contract.file.name
    contract.file = uploaded
    contract.file_original_name = safe_display_name(uploaded.name)
    contract.file_uploaded_at = timezone.now()
    contract.updated_by = user
    contract.save()
    _delete_file_later(contract.file.storage, old_name)
    return contract


@transaction.atomic
def add_document(*, document: ContractDocument, uploaded, user) -> ContractDocument:
    validate_upload(uploaded, DOCUMENT_EXTENSIONS)
    document.file = uploaded
    document.original_name = safe_display_name(uploaded.name)
    document.size = uploaded.size
    document.uploaded_by = user
    document.uploaded_at = timezone.now()
    document.full_clean(exclude=['file'])
    document.save()
    return document
