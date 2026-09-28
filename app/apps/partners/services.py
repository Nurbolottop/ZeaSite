"""Бизнес-логика кандидатов и партнёров. Views вызывают только эти функции."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    CandidateAssessment, CandidateDecision, Company, CompanyContact,
    CompanyStatus, CompanyStatusHistory, DecisionResult,
)

S = CompanyStatus

# Допустимые переходы воронки. Возвраты на шаг назад разрешены
# (переговоры сорвались, нужен повторный анализ и т.п.).
TRANSITIONS = {
    S.NEW:         (S.ANALYSIS, S.REJECTED),
    S.ANALYSIS:    (S.DISCUSSION, S.REJECTED),
    S.DISCUSSION:  (S.APPROVED, S.ANALYSIS, S.REJECTED),
    S.APPROVED:    (S.NEGOTIATION, S.REJECTED),
    S.NEGOTIATION: (S.CONTRACT, S.APPROVED, S.REJECTED),
    S.CONTRACT:    (S.PARTNER, S.NEGOTIATION, S.REJECTED),
    S.PARTNER:     (),               # завершение партнёрства — будущий этап
    S.REJECTED:    (S.NEW,),         # вернуть в работу
}

# Сам акт одобрения — только решением команды. Возврат «Переговоры → Одобрен»
# (кандидат уже был одобрен ранее) остаётся ручным.
DECISION_ONLY_TRANSITIONS = {(S.DISCUSSION, S.APPROVED)}

# Оформление партнёрства — отдельное действие «Оформить как партнёра»
# (make_partner), а не пункт обычной смены статуса. Требует ACTIVE-договор.
PARTNER_TRANSITION = (S.CONTRACT, S.PARTNER)

# Статусы, в которых команда рассматривает кандидата.
DECISION_STATUSES = {S.ANALYSIS, S.DISCUSSION}

# Кандидаты «в работе» — всё, кроме партнёров и отклонённых.
PIPELINE_STATUSES = (S.NEW, S.ANALYSIS, S.DISCUSSION, S.APPROVED, S.NEGOTIATION, S.CONTRACT)


def allowed_transitions(company, *, manual=True):
    """Статусы, в которые можно перевести компанию из текущего."""
    targets = TRANSITIONS.get(company.status, ())
    if manual:
        targets = tuple(t for t in targets
                        if (company.status, t) not in DECISION_ONLY_TRANSITIONS
                        and (company.status, t) != PARTNER_TRANSITION)
    return targets


def _check_manager(company):
    from .selectors import manager_choices
    if company.manager_id and not manager_choices().filter(pk=company.manager_id).exists():
        raise ValidationError({'manager': 'Ответственным может быть только Руководитель '
                                          'или Менеджер по развитию.'})


def has_active_contract(company) -> bool:
    from apps.contracts.selectors import active_contract
    return active_contract(company) is not None


def _log_status(company, from_status, to_status, user, comment, at):
    return CompanyStatusHistory.objects.create(
        company=company, from_status=from_status, to_status=to_status,
        changed_by=user, changed_at=at, comment=comment,
    )


@transaction.atomic
def create_company(*, company: Company, user) -> Company:
    """Новая компания всегда начинает воронку со статуса «Новый»."""
    now = timezone.now()
    company.status = S.NEW
    company.status_changed_at = now
    company.created_by = user
    company.updated_by = user
    company.full_clean()
    _check_manager(company)
    company.save()
    _log_status(company, '', S.NEW, user, 'Компания добавлена', now)
    return company


def update_company(*, company: Company, user) -> Company:
    """Сохранение основных данных. Статус здесь не меняется."""
    company.updated_by = user
    company.full_clean()
    # Проверяем только смену ответственного: бывший менеджер, лишённый роли,
    # не должен блокировать правку остальных полей
    previous = Company.objects.filter(pk=company.pk).values_list('manager_id', flat=True).first()
    if company.manager_id != previous:
        _check_manager(company)
    company.save()
    return company


@transaction.atomic
def change_status(*, company: Company, to_status: str, user, comment: str = '',
                  _by_decision: bool = False) -> CompanyStatusHistory:
    """Единственная точка смены статуса компании.

    Проверяет переход, требует причину для отклонения, пишет историю.
    """
    comment = (comment or '').strip()
    # Блокируем строку: два одновременных перехода не должны проскочить оба
    locked = Company.objects.select_for_update().get(pk=company.pk)
    from_status = locked.status

    if to_status not in S.values:
        raise ValidationError({'to_status': 'Неизвестный статус.'})
    if to_status not in TRANSITIONS.get(from_status, ()):
        raise ValidationError({'to_status': (
            f'Нельзя перевести из «{S(from_status).label}» в «{S(to_status).label}».'
        )})
    if (from_status, to_status) in DECISION_ONLY_TRANSITIONS and not _by_decision:
        raise ValidationError({'to_status': (
            f'Статус «{S(to_status).label}» устанавливается только решением команды.'
        )})
    if to_status == S.REJECTED and not comment:
        raise ValidationError({'comment': 'Укажите причину отклонения.'})
    if to_status == S.PARTNER and not has_active_contract(locked):
        raise ValidationError({'to_status': 'Партнёром компания становится только при '
                                            'действующем (ACTIVE) договоре.'})

    now = timezone.now()
    locked.status = to_status
    locked.status_changed_at = now
    locked.updated_by = user
    locked.save(update_fields=['status', 'status_changed_at', 'updated_by', 'updated_at'])

    # Синхронизируем объект, который держит вызывающий код
    company.status = locked.status
    company.status_changed_at = locked.status_changed_at
    company.updated_by = user
    company.updated_at = locked.updated_at
    return _log_status(company, from_status, to_status, user, comment, now)


def make_partner(*, company: Company, user, comment: str = '') -> CompanyStatusHistory:
    """«Оформить как партнёра»: CONTRACT → PARTNER после подтверждения пользователем.

    Наличие ACTIVE-договора проверяет change_status().
    """
    if company.status != S.CONTRACT:
        raise ValidationError('Оформить партнёрство можно только на стадии «Договор».')
    return change_status(company=company, to_status=S.PARTNER, user=user,
                         comment=comment or 'Партнёрство оформлено по действующему договору')


@transaction.atomic
def make_decision(*, company: Company, decision: str, user, comment: str = '',
                  review_date=None) -> CandidateDecision:
    """Фиксирует решение команды и двигает воронку:

    «Одобрить»     → статус «Одобрен» (не «Партнёр»: дальше переговоры и договор);
    «Отклонить»    → «Отклонён», комментарий обязателен;
    «На доработку» → из «Обсуждения» назад в «Анализ», иначе статус не меняется.
    """
    comment = (comment or '').strip()
    if company.status not in DECISION_STATUSES:
        raise ValidationError(
            'Решение принимается на стадиях «Анализ» или «Обсуждение», '
            f'сейчас — «{company.get_status_display()}».'
        )
    if decision not in DecisionResult.values:
        raise ValidationError({'decision': 'Неизвестное решение.'})
    if decision == DecisionResult.APPROVE and company.status != S.DISCUSSION:
        raise ValidationError({'decision': 'Одобрить можно только после обсуждения: '
                                           'сначала переведите кандидата в «Обсуждение».'})
    if decision == DecisionResult.REJECT and not comment:
        raise ValidationError({'comment': 'Укажите причину отклонения.'})

    record = CandidateDecision(
        company=company, decision=decision, comment=comment,
        review_date=review_date or timezone.localdate(),
        created_by=user, updated_by=user,
    )
    record.full_clean()
    record.save()

    history_comment = f'Решение команды: {record.get_decision_display()}'
    if comment:
        history_comment += f'. {comment}'
    if decision == DecisionResult.APPROVE:
        change_status(company=company, to_status=S.APPROVED, user=user,
                      comment=history_comment, _by_decision=True)
    elif decision == DecisionResult.REJECT:
        change_status(company=company, to_status=S.REJECTED, user=user, comment=history_comment)
    elif company.status == S.DISCUSSION:
        change_status(company=company, to_status=S.ANALYSIS, user=user, comment=history_comment)
    return record


@transaction.atomic
def save_contact(*, contact: CompanyContact) -> CompanyContact:
    """Создание/изменение контакта. Основной контакт у компании только один."""
    contact.full_clean(validate_constraints=False)
    if contact.is_primary:
        (CompanyContact.objects
         .filter(company=contact.company, is_primary=True)
         .exclude(pk=contact.pk)
         .update(is_primary=False))
    contact.save()
    return contact


def delete_contact(*, contact: CompanyContact) -> None:
    contact.delete()


def save_assessment(*, assessment: CandidateAssessment, user) -> CandidateAssessment:
    if assessment.pk is None:
        assessment.created_by = user
    assessment.updated_by = user
    assessment.full_clean()
    assessment.save()
    return assessment
