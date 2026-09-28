"""Централизованная проверка доступа.

Все проверки ролей идут через функции этого модуля — во view, меню и
шаблонах напрямую user.groups не проверяем.
"""
from django.core.exceptions import ImproperlyConfigured

from .roles import ALL_ROLES, Role

# Доступ к модулям: ключ модуля → роли, которым он открыт.
# None — любой авторизованный пользователь (даже без роли).
#
# ВНИМАНИЕ: матрица предварительная — пока все модули открыты всем 6 ролям.
# Окончательно фиксируется при разработке каждого модуля.
MODULE_ACCESS = {
    'dashboard':  None,
    'candidates': ALL_ROLES,
    'partners':   ALL_ROLES,
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
