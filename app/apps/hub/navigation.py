"""Единый реестр разделов ZEA Hub: из него строятся sidebar и URL заглушек.

Видимость пункта меню определяется той же матрицей, что и доступ к view
(apps.users.access.MODULE_ACCESS), поэтому меню и права не расходятся.
"""
from dataclasses import dataclass

from apps.users.access import can_access_module


@dataclass(frozen=True)
class NavItem:
    module: str      # ключ из MODULE_ACCESS
    title: str
    icon: str        # имя иконки Bootstrap Icons
    url_name: str    # полное имя с namespace, например 'candidates:list'
    ready: bool = False  # False → раздел в разработке (страница-заглушка)


NAVIGATION = (
    NavItem('dashboard',  'Dashboard',  'grid-1x2',         'hub:dashboard', ready=True),
    NavItem('candidates', 'Кандидаты',  'person-plus',      'candidates:list', ready=True),
    NavItem('partners',   'Партнёры',   'building',         'partners:list', ready=True),
    NavItem('projects',   'Проекты',    'kanban',           'hub:projects'),
    NavItem('team',       'Команда',    'people',           'hub:team'),
    NavItem('contracts',  'Договоры',   'file-earmark-text', 'contracts:list', ready=True),
    NavItem('finance',    'Финансы',    'cash-stack',       'hub:finance'),
    NavItem('expenses',   'Расходы',    'receipt',          'hub:expenses'),
    NavItem('reports',    'Отчёты',     'bar-chart-line',   'hub:reports'),
)

NAV_BY_MODULE = {item.module: item for item in NAVIGATION}


def resolve_active_module(request):
    """Активный раздел: явно заданный view (request.hub_active_module),
    иначе по URL — точное совпадение имени или namespace модуля."""
    explicit = getattr(request, 'hub_active_module', None)
    if explicit:
        return explicit
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return None
    for item in NAVIGATION:
        if match.view_name == item.url_name:
            return item.module
    namespace = match.namespace
    if namespace and namespace != 'hub':
        for item in NAVIGATION:
            if item.url_name.split(':')[0] == namespace:
                return item.module
    return None


def build_menu(user, active_module=None):
    """Пункты меню, доступные пользователю."""
    return [
        {'item': item, 'active': item.module == active_module}
        for item in NAVIGATION
        if can_access_module(user, item.module)
    ]
