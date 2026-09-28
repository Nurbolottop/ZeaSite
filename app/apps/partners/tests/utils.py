from django.contrib.auth.models import Group, User

from apps.partners import services
from apps.partners.models import Company, CompanyStatus
from apps.users.roles import Role

S = CompanyStatus

# Путь по воронке до каждого статуса (APPROVED — только решением команды)
PATH = [S.ANALYSIS, S.DISCUSSION, S.APPROVED, S.NEGOTIATION, S.CONTRACT, S.PARTNER]


def make_user(username, *roles, **extra):
    user = User.objects.create_user(username, password='pass-12345', **extra)
    if roles:
        user.groups.add(*Group.objects.filter(name__in=roles))
    return user


def make_company(user, name='Альфа', **fields):
    return services.create_company(company=Company(name=name, **fields), user=user)


def move_to(company, target, user):
    """Проводит компанию по воронке от текущего статуса до target."""
    start = PATH.index(company.status) + 1 if company.status in PATH else 0
    for status in PATH[start:PATH.index(target) + 1]:
        if status == S.APPROVED:
            services.make_decision(company=company, decision='approve', user=user)
        else:
            services.change_status(company=company, to_status=status, user=user)
    company.refresh_from_db()
    return company


def head(username='head'):
    return make_user(username, Role.HEAD, first_name='Руководитель')
