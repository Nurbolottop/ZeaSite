from django import template
from django.utils.html import format_html

from apps.partners.models import CompanyStatus, CompanyType

register = template.Library()


@register.filter
def status_badge(status):
    """{{ company.status|status_badge }} → цветной badge статуса."""
    if not status:
        return '—'
    return format_html('<span class="zh-status zh-status-{}">{}</span>',
                       status, CompanyStatus(status).label)


@register.filter
def type_label(company_type):
    return CompanyType(company_type).label if company_type else '—'
