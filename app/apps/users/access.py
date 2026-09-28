"""Централизованная проверка доступа.

Все проверки ролей идут через функции этого модуля — во view, меню и
шаблонах напрямую user.groups не проверяем.
"""
from django.core.exceptions import ImproperlyConfigured

from .roles import ALL_ROLES, Role

# Действия внутри модулей: '<модуль>.<действие>' → роли.
# Superuser проходит любую проверку (см. has_role).
PERMISSIONS = {
    # Кандидаты и партнёры (apps.partners)
    'partners.view':   (Role.HEAD, Role.BIZDEV, Role.PM, Role.TECH_LEAD, Role.MARKETING),
    # создание/редактирование компании, контакты, анализ, смена статусов
    'partners.edit':   (Role.HEAD, Role.BIZDEV),
    # решение команды по кандидату (одобрить / отклонить / на доработку)
    'partners.decide': (Role.HEAD,),
}

# Доступ к модулям (разделам меню): ключ модуля → роли, которым он открыт.
# None — любой авторизованный пользователь (даже без роли).
#
# Модули без утверждённой матрицы пока открыты всем 6 ролям.
MODULE_ACCESS = {
    'dashboard':  None,
    'candidates': PERMISSIONS['partners.view'],
    'partners':   PERMISSIONS['partners.view'],
    'projects':   ALL_ROLES,
    'team':       ALL_ROLES,
    'contracts':  ALL_ROLES,
    'finance':    ALL_ROLES,
    'expenses':   ALL_ROLES,
    'reports':    ALL_ROLES,
}

_CACHE_ATTR = '_zea_group_names'


def get_group_names(user):
    """Имена всех групп пользователя (кэшируются на объекте на время запроса)."""
    if not user.is_authenticated:
        return frozenset()
    if not hasattr(user, _CACHE_ATTR):
        setattr(user, _CACHE_ATTR, frozenset(user.groups.values_list('name', flat=True)))
    return getattr(user, _CACHE_ATTR)


def get_user_roles(user):
    """Роли ZEA Hub пользователя в порядке ALL_ROLES."""
    names = get_group_names(user)
    return [role for role in ALL_ROLES if role in names]


def has_role(user, *roles):
    """True, если у пользователя есть хотя бы одна из ролей. Superuser — всегда True."""
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return not get_group_names(user).isdisjoint(roles)


def is_head(user):
    return has_role(user, Role.HEAD)


def can_access_module(user, module):
    """Доступ к модулю по матрице MODULE_ACCESS."""
    if module not in MODULE_ACCESS:
        raise ImproperlyConfigured(f'Модуль «{module}» не описан в MODULE_ACCESS')
    if not user.is_authenticated or not user.is_active:
        return False
    roles = MODULE_ACCESS[module]
    if roles is None:
        return True
    return has_role(user, *roles)


def has_permission(user, permission):
    """Право на действие по матрице PERMISSIONS."""
    if permission not in PERMISSIONS:
        raise ImproperlyConfigured(f'Право «{permission}» не описано в PERMISSIONS')
    return has_role(user, *PERMISSIONS[permission])
