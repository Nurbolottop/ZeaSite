"""Бизнес-логика проектов. Права проверяются здесь (через permissions.py),
поэтому прямой POST в обход формы их не обходит."""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.contracts.models import ContractStatus
from apps.partners.models import CompanyStatus
from apps.users.roles import Role

from . import permissions as perms
from .models import (
    Project, ProjectMember, ProjectStatus, ProjectStatusHistory,
    ProjectTechnicalInfo,
)

P = ProjectStatus

# Основной путь и разрешённые возвраты. Пауза и отмена — из любого рабочего статуса.
TRANSITIONS = {
    P.PLANNING:    (P.DEVELOPMENT,),
    P.DEVELOPMENT: (P.TESTING,),
    P.TESTING:     (P.MVP, P.DEVELOPMENT),
    P.MVP:         (P.LAUNCHED, P.DEVELOPMENT, P.TESTING),
    P.LAUNCHED:    (P.SUPPORT,),
    P.SUPPORT:     (),
}
REASON_REQUIRED = {P.PAUSED, P.CANCELLED}

# Поля, которые меняет только Руководитель
CORE_FIELDS = ('company_id', 'contract_id', 'name', 'code', 'pm_id', 'technical_lead_id')
# Рабочие поля — Руководитель и PM проекта
WORK_FIELDS = ('description', 'project_type', 'project_type_other', 'priority',
               'start_date', 'planned_end_date', 'actual_end_date', 'notes')


def users_with_role(role):
    return (get_user_model().objects.filter(is_active=True, groups__name=role)
            .distinct().order_by('first_name', 'last_name', 'username'))


def _check_assignees(project):
    errors = {}
    if not users_with_role(Role.PM).filter(pk=project.pm_id).exists():
        errors['pm'] = 'PM проекта может быть только активный пользователь с ролью «Проектный менеджер (PM)».'
    if not users_with_role(Role.TECH_LEAD).filter(pk=project.technical_lead_id).exists():
        errors['technical_lead'] = ('Техническим руководителем может быть только активный пользователь '
                                    'с ролью «Технический руководитель».')
    if errors:
        raise ValidationError(errors)


def _check_contract(project):
    contract = project.contract
    if contract.status != ContractStatus.ACTIVE:
        raise ValidationError({'contract': 'Проект ведётся на основании действующего (ACTIVE) договора.'})
    if contract.company.status != CompanyStatus.PARTNER:
        raise ValidationError({'contract': 'Проекты создаются только для компаний со статусом «Партнёр».'})


def _log(project, from_status, to_status, user, comment, at):
    return ProjectStatusHistory.objects.create(project=project, from_status=from_status,
                                               to_status=to_status, changed_by=user,
                                               changed_at=at, comment=comment)


@transaction.atomic
def create_project(*, project: Project, user) -> Project:
    if not perms.can_create(user):
        raise PermissionDenied('Создавать проекты может только Руководитель.')
    if project.contract_id is None:
        raise ValidationError({'contract': 'Выберите договор.'})
    project.company = project.contract.company  # компания проекта = компания договора
    _check_contract(project)
    now = timezone.now()
    project.status = P.PLANNING
    project.status_changed_at = now
    project.paused_from_status = ''
    project.created_by = project.updated_by = user
    project.full_clean()
    _check_assignees(project)
    project.save()
    _log(project, '', P.PLANNING, user, 'Проект создан', now)
    return project


@transaction.atomic
def update_project(*, project: Project, user) -> Project:
    current = Project.objects.select_for_update().get(pk=project.pk)
    changed = {f for f in CORE_FIELDS + WORK_FIELDS if getattr(project, f) != getattr(current, f)}
    if changed & set(CORE_FIELDS) and not perms.can_edit_core(user):
        raise PermissionDenied('Компанию, договор, название, код, PM и технического руководителя '
                               'меняет только Руководитель.')
    if changed and not perms.can_edit_work(user, current):
        raise PermissionDenied('Нет права редактировать проект.')
    if 'contract_id' in changed:
        project.company = project.contract.company
        _check_contract(project)
    project.status = current.status  # статус — только change_project_status()
    project.paused_from_status = current.paused_from_status
    project.launch_date = current.launch_date
    project.updated_by = user
    project.full_clean()
    if {'pm_id', 'technical_lead_id'} & changed:
        _check_assignees(project)
    project.save()
    return project


def allowed_transitions(project, user):
    if not perms.can_change_status(user, project):
        return ()
    if project.status == P.CANCELLED:
        return ()
    if project.status == P.PAUSED:
        targets = (project.paused_from_status or P.PLANNING, P.CANCELLED)
    else:
        targets = TRANSITIONS.get(project.status, ()) + (P.PAUSED, P.CANCELLED)
    if not perms.can_cancel(user, project):
        targets = tuple(t for t in targets if t != P.CANCELLED)
    return targets


@transaction.atomic
def change_project_status(*, project: Project, to_status: str, user,
                          comment: str = '') -> ProjectStatusHistory:
    """Единственная точка смены статуса проекта."""
    comment = (comment or '').strip()
    locked = Project.objects.select_for_update().get(pk=project.pk)
    if not perms.can_change_status(user, locked):
        raise PermissionDenied('Менять статус проекта могут Руководитель и PM проекта.')
    if to_status == P.CANCELLED and not perms.can_cancel(user, locked):
        raise PermissionDenied('Отменить проект может только Руководитель.')
    from_status = locked.status
    if to_status not in P.values:
        raise ValidationError({'to_status': 'Неизвестный статус.'})
    if to_status not in allowed_transitions(locked, user):
        raise ValidationError({'to_status': (
            f'Нельзя перевести проект из «{P(from_status).label}» в «{P(to_status).label}».'
        )})
    if to_status in REASON_REQUIRED and not comment:
        label = 'приостановки' if to_status == P.PAUSED else 'отмены'
        raise ValidationError({'comment': f'Укажите причину {label}.'})

    now = timezone.now()
    if to_status == P.PAUSED:
        locked.paused_from_status = from_status
    elif from_status == P.PAUSED:
        locked.paused_from_status = ''
    if to_status == P.LAUNCHED and locked.launch_date is None:
        locked.launch_date = timezone.localdate()
    locked.status = to_status
    locked.status_changed_at = now
    locked.updated_by = user
    locked.save(update_fields=['status', 'status_changed_at', 'paused_from_status', 'launch_date',
                               'updated_by', 'updated_at'])
    for field in ('status', 'status_changed_at', 'paused_from_status', 'launch_date'):
        setattr(project, field, getattr(locked, field))
    return _log(project, from_status, to_status, user, comment, now)


def save_technical_info(*, info: ProjectTechnicalInfo, user) -> ProjectTechnicalInfo:
    if not perms.can_edit_technical(user, info.project):
        raise PermissionDenied('Нет права менять техническую информацию проекта.')
    if info.pk is None:
        info.created_by = user
    info.updated_by = user
    info.full_clean()  # включает проверку на секреты
    info.save()
    return info


# ── Команда проекта ───────────────────────────────────────────────────────

def eligible_members():
    """Кого можно добавить в проект: активные пользователи с активным профилем сотрудника."""
    return (get_user_model().objects
            .filter(is_active=True, employee__is_active=True)
            .order_by('first_name', 'last_name', 'username'))


@transaction.atomic
def add_member(*, project: Project, member, specialization, user, note='') -> ProjectMember:
    scope = perms.member_scope(user, project)
    if scope is None:
        raise PermissionDenied('Нет права управлять командой проекта.')
    if scope == 'technical' and not specialization.is_technical:
        raise PermissionDenied('Технический руководитель добавляет только технических участников.')
    if project.status == P.CANCELLED:
        raise ValidationError('В отменённый проект нельзя добавлять участников.')
    if not specialization.is_active:
        raise ValidationError({'specialization': 'Эта специализация больше не используется.'})
    if not eligible_members().filter(pk=member.pk).exists():
        raise ValidationError({'member': 'Добавить можно только действующего сотрудника команды ZEA.'})
    if ProjectMember.objects.filter(project=project, member=member, specialization=specialization,
                                    is_active=True).exists():
        raise ValidationError({'member': 'Сотрудник уже в проекте с этой ролью.'})
    membership = ProjectMember(project=project, member=member, specialization=specialization,
                               note=(note or '').strip(), added_by=user)
    membership.full_clean(validate_constraints=False)
    membership.save()
    return membership


def remove_member(*, membership: ProjectMember, user) -> ProjectMember:
    """Участник выводится из проекта (запись остаётся в истории участия)."""
    scope = perms.member_scope(user, membership.project)
    if scope is None or (scope == 'technical' and not membership.specialization.is_technical):
        raise PermissionDenied('Нет права убрать этого участника.')
    if not membership.is_active:
        raise ValidationError('Участник уже выведен из проекта.')
    membership.is_active = False
    membership.left_at = timezone.localdate()
    membership.save(update_fields=['is_active', 'left_at'])
    return membership
