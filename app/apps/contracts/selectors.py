"""Выборки договоров."""
from django.db.models import Count, Q

from apps.partners.models import Company

from .models import Contract, ContractStatus
from .services import COMPANY_STATUSES_FOR_CONTRACT

C = ContractStatus

SORT_OPTIONS = {
    '-created': ('-created_at',),
    '-start': ('-start_date', '-created_at'),
    'start': ('start_date', 'created_at'),
    'number': ('number',),
    'company': ('company__name', '-created_at'),
}
DEFAULT_SORT = '-created'


def contract_list(*, search='', company_id=None, status='', date_from=None, date_to=None,
                  sort=DEFAULT_SORT):
    qs = Contract.objects.select_related('company', 'created_by')
    if search:
        qs = qs.filter(Q(number__icontains=search) | Q(company__name__icontains=search))
    if company_id:
        qs = qs.filter(company_id=company_id)
    if status:
        qs = qs.filter(status=status)
    # Период: договор действовал хотя бы день в [date_from, date_to]
    if date_from:
        qs = qs.filter(Q(end_date__isnull=True) | Q(end_date__gte=date_from))
    if date_to:
        qs = qs.filter(start_date__lte=date_to)
    return qs.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS[DEFAULT_SORT]))


def contract_detail(pk):
    return (Contract.objects.select_related('company', 'created_by', 'updated_by')
            .prefetch_related('status_history__changed_by', 'documents__uploaded_by')
            .get(pk=pk))


def active_contract(company):
    return Contract.objects.filter(company=company, status=C.ACTIVE).first()


def company_contracts(company):
    return Contract.objects.filter(company=company).order_by('-created_at')


def company_contract_state(contracts):
    """Короткая сводка для карточки компании на стадии «Договор»."""
    statuses = {c.status for c in contracts}
    for status, label in ((C.ACTIVE, 'Действует'), (C.READY, 'Готов к подписанию'),
                          (C.REVIEW, 'На согласовании'), (C.DRAFT, 'Черновик')):
        if status in statuses:
            return status, label
    return '', 'Нет договора'


def companies_for_new_contract():
    return Company.objects.filter(status__in=COMPANY_STATUSES_FOR_CONTRACT).order_by('name')


def companies_with_contracts():
    return Company.objects.filter(contracts__isnull=False).distinct().order_by('name')


def dashboard_stats():
    counts = dict(Contract.objects.values_list('status').annotate(n=Count('id')).order_by())
    return {'review': counts.get(C.REVIEW, 0), 'ready': counts.get(C.READY, 0),
            'active': counts.get(C.ACTIVE, 0)}
