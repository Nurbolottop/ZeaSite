"""Объектные права на проекты. Все проверки «может ли пользователь X сделать Y
с проектом P» — только здесь. Основаны на ролях из apps.users.access.

Кто что видит:
- Руководитель, Менеджер по развитию, Маркетинг — все проекты (projects.view_all);
- PM, Технический руководитель, DevOps и прочие — только «свои»: где они PM,
  технический руководитель или активный участник команды.
Маркетинг видит сокращённую карточку (limited): без команды, техинфо, заметок.
"""
from django.db.models import Q

from apps.users.access import has_permission, has_role
from apps.users.roles import Role


def is_head(user):
    return has_permission(user, 'projects.manage_all')  # Руководитель или superuser


def _involvement_q(user):
    return (Q(pm=user) | Q(technical_lead=user)
            | Q(members__member=user, members__is_active=True))


def scope_projects(qs, user):
    """Проекты, которые пользователь вправе видеть."""
    if not has_permission(user, 'projects.view'):
        return qs.none()
    if has_permission(user, 'projects.view_all'):
        return qs
    return qs.filter(_involvement_q(user)).distinct()


def is_pm_of(user, project):
    return project.pm_id == user.pk and has_role(user, Role.PM)


def is_tech_lead_of(user, project):
    return project.technical_lead_id == user.pk and has_role(user, Role.TECH_LEAD)


def is_active_member(user, project):
    return project.members.filter(member=user, is_active=True).exists()


def is_involved(user, project):
    return (project.pm_id == user.pk or project.technical_lead_id == user.pk
            or is_active_member(user, project))


def can_view(user, project):
    if not has_permission(user, 'projects.view'):
        return False
    return has_permission(user, 'projects.view_all') or is_involved(user, project)


def is_limited(user, project):
    """Сокращённая карточка: видит проект только благодаря роли «Маркетинг»."""
    if is_head(user) or has_role(user, Role.BIZDEV):
        return False
    if is_involved(user, project):
        return False
    return has_role(user, Role.MARKETING)


def can_edit_work(user, project):
    """Рабочие данные: описание, тип, приоритет, сроки, заметки."""
    return is_head(user) or is_pm_of(user, project)


def can_edit_core(user):
    """Компания, договор, название, код, PM, технический руководитель."""
    return is_head(user)


def can_change_status(user, project):
    return is_head(user) or is_pm_of(user, project)


def can_cancel(user, project):
    return is_head(user)


def can_view_technical(user, project):
    return is_head(user) or is_involved(user, project)


def can_edit_technical(user, project):
    return is_head(user) or is_pm_of(user, project) or is_tech_lead_of(user, project)


def member_scope(user, project):
    """Каких участников пользователь может добавлять/убирать:
    'all' — любых, 'technical' — только с технической специализацией, None — никаких."""
    if is_head(user) or is_pm_of(user, project):
        return 'all'
    if is_tech_lead_of(user, project):
        return 'technical'
    return None


def can_view_team(user, project):
    return can_view(user, project) and not is_limited(user, project)


def can_view_notes(user, project):
    return can_view(user, project) and not is_limited(user, project)


def can_create(user):
    return is_head(user)
