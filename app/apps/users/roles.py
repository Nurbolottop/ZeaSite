"""Роли ZEA Hub.

Роль = Django Group с таким же именем. Группы создаются миграцией
users/0002_create_roles. Пользователь может состоять в нескольких группах.
Не переименовывайте группы в админке — код ссылается на эти имена.
"""


class Role:
    HEAD = 'Руководитель / Финансы и аналитика'
    BIZDEV = 'Менеджер по развитию'
    PM = 'Проектный менеджер (PM)'
    TECH_LEAD = 'Технический руководитель'
    MARKETING = 'Маркетинг / Бренд'
    DEVOPS = 'DevOps'


# Порядок важен: так роли выводятся в интерфейсе
ALL_ROLES = (
    Role.HEAD,
    Role.BIZDEV,
    Role.PM,
    Role.TECH_LEAD,
    Role.MARKETING,
    Role.DEVOPS,
)
