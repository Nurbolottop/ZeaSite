from django import template
from django.utils.html import format_html

from apps.contracts.models import CalculationBase, ContractStatus

register = template.Library()


@register.filter
def contract_status_badge(status):
    if not status:
        return '—'
    return format_html('<span class="zh-status zh-cstatus-{}">{}</span>',
                       status, ContractStatus(status).label)


@register.filter
def base_label(value):
    return CalculationBase(value).label if value else '—'


@register.filter
def percent(value):
    """Decimal → «12,5 %» без лишних нулей."""
    if value is None:
        return '—'
    text = format(value.normalize(), 'f').replace('.', ',')
    return f'{text} %'


@register.filter
def filesize(num):
    num = num or 0
    for unit in ('Б', 'КБ', 'МБ'):
        if num < 1024:
            return f'{num:.0f} {unit}'
        num /= 1024
    return f'{num:.1f} ГБ'
