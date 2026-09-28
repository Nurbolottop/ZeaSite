"""Выборки проектов. Любая выборка для пользователя проходит через scope_projects()."""
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils import timezone

from apps.contracts.models import Contract, ContractStatus
from apps.partners.models import Company, CompanyStatus
from apps.users.roles import Role

from .models import PRIORITY_ORDER, Project, ProjectStatus
from .permissions import scope_projects
from .services import users_with_role

P = ProjectStatus

# Активные проекты — в работе (без паузы и отмены)
ACTIVE_STATUSES = (P.PLANNING, P.DEVELOPMENT, P.TESTING, P.MVP, P.LAUNCHED, P.SUPPORT)
# До запуска — для контроля просроченного планового срока
PRE_LAUNCH_STATUSES = (P.PLANNING, P.DEVELOPMENT, P.TESTING, P.MVP)

_PRIORITY = Case(*[When(priority=p, then=Value(i)) for p, i in PRIORITY_ORDER.items()],
                 output_field=IntegerField())
_STATUS = Case(*[When(status=s, then=Value(i)) for i, s in enumerate(P.values)],
               output_field=IntegerField())

SORT_OPTIONS = {
    '-updated': ('-updated_at',),
    'priority': ('priority_order', 'planned_end_date'),
    'deadline': ('planned_end_date', 'priority_order'),
    'name': ('name',),
    'status': ('status_order', 'name'),
    '-created': ('-created_at',),
}
DEFAULT_SORT = 'priority'


def _base(user):
    qs = (Project.objects.select_related('company', 'pm', 'technical_lead')
          .annotate(priority_order=_PRIORITY, status_order=_STATUS))
    return scope_projects(qs, user)


def project_list(user, *, search='', company_id=None, status='', project_type='', pm_id=None,
                 technical_lead_id=None, priority='', sort=DEFAULT_SORT):
    qs = _base(user)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search)
                       | Q(company__name__icontains=search))
    if company_id:
        qs = qs.filter(company_id=company_id)
    if status == 'active':
        qs = qs.filter(status__in=ACTIVE_STATUSES)
    elif status == 'overdue':
        qs = qs.filter(status__in=PRE_LAUNCH_STATUSES, actual_end_date__isnull=True,
                       planned_end_date__lt=timezone.localdate())
    elif status:
        qs = qs.filter(status=status)
    if project_type:
        qs = qs.filter(project_type=project_type)
    if pm_id:
        qs = qs.filter(pm_id=pm_id)
    if technical_lead_id:
        qs = qs.filter(technical_lead_id=technical_lead_id)
    if priority:
        qs = qs.filter(priority=priority)
    return qs.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT]))


def project_detail(pk):
    return (Project.objects
            .select_related('company', 'contract', 'pm', 'technical_lead', 'created_by', 'updated_by')
            .prefetch_related('status_history__changed_by', 'members__member', 'members__specialization')
            .get(pk=pk))


def company_projects(company, user):
    return _base(user).filter(company=company).order_by('status_order', 'name')


def active_contracts_for_projects():
    """Договоры, на основании которых можно открыть проект."""
    return (Contract.objects.filter(status=ContractStatus.ACTIVE, company__status=CompanyStatus.PARTNER)
            .select_related('company').order_by('company__name', 'number'))


def companies_with_projects(user):
    ids = _base(user).values('company_id')
    return Company.objects.filter(pk__in=ids).order_by('name')


def pm_choices():
    return users_with_role(Role.PM)


def tech_lead_choices():
    return users_with_role(Role.TECH_LEAD)


def user_active_projects(user_obj):
    """Активные проекты сотрудника: PM, технический руководитель или участник."""
    return (Project.objects
            .filter(Q(pm=user_obj) | Q(technical_lead=user_obj)
                    | Q(members__member=user_obj, members__is_active=True),
                    status__in=ACTIVE_STATUSES)
            .select_related('company').distinct().order_by('name'))


def dashboard_stats(user):
    qs = _base(user)
    counts = dict(qs.order_by().values_list('status').annotate(n=Count('id', distinct=True)))
    return {
        'active': sum(counts.get(s, 0) for s in ACTIVE_STATUSES),
        'development': counts.get(P.DEVELOPMENT, 0),
        'testing': counts.get(P.TESTING, 0),
        'support': counts.get(P.SUPPORT, 0),
        'paused': counts.get(P.PAUSED, 0),
        'overdue': qs.filter(status__in=PRE_LAUNCH_STATUSES, actual_end_date__isnull=True,
                             planned_end_date__lt=timezone.localdate()).count(),
    }
