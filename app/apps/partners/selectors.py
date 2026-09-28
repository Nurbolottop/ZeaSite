"""Выборки кандидатов и партнёров для списков, карточки и Dashboard."""
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, IntegerField, Q, Value, When

from apps.users.access import PERMISSIONS

from .models import Company, CompanyStatus
from .services import PIPELINE_STATUSES

S = CompanyStatus

# Порядок статусов в воронке — для сортировки «по статусу»
_STATUS_ORDER = Case(
    *[When(status=value, then=Value(i)) for i, value in enumerate(S.values)],
    output_field=IntegerField(),
)

SORT_OPTIONS = {
    '-updated': ('-updated_at',),
    '-created': ('-created_at',),
    'created': ('created_at',),
    'name': ('name',),
    '-name': ('-name',),
    'status': ('status_order', 'name'),
    '-status': ('-status_order', 'name'),
}
DEFAULT_SORT = '-updated'


def _base_qs():
    return Company.objects.select_related('manager').annotate(status_order=_STATUS_ORDER)


def filter_companies(qs, *, search='', company_type='', manager_id=None, sort=DEFAULT_SORT):
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(legal_name__icontains=search))
    if company_type:
        qs = qs.filter(company_type=company_type)
    if manager_id == 'none':
        qs = qs.filter(manager__isnull=True)
    elif manager_id:
        qs = qs.filter(manager_id=manager_id)
    return qs.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT]))


def candidate_list(*, status='', **filters):
    """Кандидаты. По умолчанию — активная воронка (без отклонённых);
    партнёры сюда не попадают никогда — они в разделе «Партнёры»."""
    qs = _base_qs().exclude(status=S.PARTNER)
    if status == 'all':
        pass
    elif status:
        qs = qs.filter(status=status)
    else:
        qs = qs.filter(status__in=PIPELINE_STATUSES)
    return filter_companies(qs, **filters)


def partner_list(**filters):
    return filter_companies(_base_qs().filter(status=S.PARTNER), **filters)


def companies_of_manager(user):
    return _base_qs().filter(manager=user)


def company_detail(pk):
    return (Company.objects
            .select_related('manager', 'created_by', 'updated_by', 'assessment')
            .prefetch_related('contacts', 'status_history__changed_by', 'decisions__created_by')
            .get(pk=pk))


def candidate_status_filter_choices():
    """Фильтр статуса в списке кандидатов (без «Партнёр»)."""
    return [('', 'В работе'), ('all', 'Все, включая отклонённых')] + [
        (value, label) for value, label in S.choices if value != S.PARTNER
    ]


def manager_choices():
    """Кого можно назначить ответственным: руководитель и менеджеры по развитию."""
    return (get_user_model().objects
            .filter(is_active=True)
            .filter(Q(groups__name__in=PERMISSIONS['partners.edit']) | Q(is_superuser=True))
            .distinct()
            .order_by('first_name', 'last_name', 'username'))


def dashboard_stats():
    counts = dict(Company.objects.values_list('status').annotate(n=Count('id')).order_by())
    pipeline = [
        {'value': value, 'label': S(value).label, 'count': counts.get(value, 0)}
        for value in PIPELINE_STATUSES
    ]
    return {
        'candidates_total': sum(item['count'] for item in pipeline),
        'analysis': counts.get(S.ANALYSIS, 0),
        'negotiation': counts.get(S.NEGOTIATION, 0),
        'partners': counts.get(S.PARTNER, 0),
        'rejected': counts.get(S.REJECTED, 0),
        'pipeline': pipeline,
    }
