from datetime import date

from apps.contracts.models import Contract, ContractStatus
from apps.partners.tests.utils import S, head, make_company, make_user, move_to  # noqa: F401
from apps.projects import services
from apps.projects.models import Project
from apps.team.models import EmployeeProfile, Specialization
from apps.users.roles import Role  # noqa: F401


def partner_with_contract(user, name='Kargo Express'):
    """Партнёр с ACTIVE-договором (move_to создаёт договор перед PARTNER)."""
    company = move_to(make_company(user, name=name), S.PARTNER, user)
    return company, Contract.objects.get(company=company, status=ContractStatus.ACTIVE)


def employee(user, *specs, **extra):
    profile = EmployeeProfile.objects.create(user=user, **extra)
    profile.specializations.set(Specialization.objects.filter(name__in=specs))
    return profile


def spec(name):
    return Specialization.objects.get(name=name)


def make_project(creator, contract, pm, lead, code='KE-CRM', **extra):
    fields = dict(contract=contract, name='CRM для логистики', code=code, project_type='crm',
                  pm=pm, technical_lead=lead, planned_end_date=date(2027, 3, 1))
    fields.update(extra)
    return services.create_project(project=Project(**fields), user=creator)


class Team:
    """Набор пользователей всех ролей + партнёр с проектом."""

    def __init__(self):
        self.head = head()
        self.bizdev = make_user('biz', Role.BIZDEV)
        self.pm = make_user('pm', Role.PM, first_name='Пётр')
        self.pm2 = make_user('pm2', Role.PM)
        self.lead = make_user('lead', Role.TECH_LEAD, first_name='Тимур')
        self.lead2 = make_user('lead2', Role.TECH_LEAD)
        self.marketing = make_user('mkt', Role.MARKETING)
        self.devops = make_user('ops', Role.DEVOPS)
        self.devops2 = make_user('ops2', Role.DEVOPS)
        self.nobody = make_user('nobody')
        self.dev = make_user('dev', first_name='Дана')  # разработчик без роли в Hub
        for user, specs in ((self.devops, ['DevOps']), (self.devops2, ['DevOps']),
                            (self.dev, ['Backend Developer', 'QA / Tester']),
                            (self.pm, ['Project Manager']), (self.lead, ['Technical Lead'])):
            employee(user, *specs)
        self.company, self.contract = partner_with_contract(self.head)
        self.project = make_project(self.head, self.contract, self.pm, self.lead)
        self.other = make_project(self.head, self.contract, self.pm2, self.lead2, code='KE-BOT',
                                  name='Telegram-бот')
