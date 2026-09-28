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
    url_name: str    # полное имя с namespace, например 'hub:candidates'
    ready: bool = False  # False → раздел в разработке (страница-заглушка)


NAVIGATION = (
    NavItem('dashboard',  'Dashboard',  'grid-1x2',         'hub:dashboard', ready=True),
    NavItem('candidates', 'Кандидаты',  'person-plus',      'hub:candidates'),
    NavItem('partners',   'Партнёры',   'building',         'hub:partners'),
    NavItem('projects',   'Проекты',    'kanban',           'hub:projects'),
    NavItem('team',       'Команда',    'people',           'hub:team'),
    NavItem('contracts',  'Договоры',   'file-earmark-text', 'hub:contracts'),
    NavItem('finance',    'Финансы',    'cash-stack',       'hub:finance'),
    NavItem('expenses',   'Расходы',    'receipt',          'hub:expenses'),
    NavItem('reports',    'Отчёты',     'bar-chart-line',   'hub:reports'),
)

NAV_BY_MODULE = {item.module: item for item in NAVIGATION}


def build_menu(user, current_view_name=None):
    """Пункты меню, доступные пользователю."""
    return [
        {'item': item, 'active': item.url_name == current_view_name}
        for item in NAVIGATION
        if can_access_module(user, item.module)
    ]
