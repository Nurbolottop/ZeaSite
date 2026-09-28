from django import template
from django.utils.html import format_html

from apps.projects.models import Priority, ProjectStatus

register = template.Library()


@register.filter
def project_status_badge(status):
    if not status:
        return '—'
    return format_html('<span class="zh-status zh-pstatus-{}">{}</span>', status, ProjectStatus(status).label)


@register.filter
def priority_badge(priority):
    if not priority:
        return '—'
    return format_html('<span class="zh-priority zh-priority-{}">{}</span>', priority, Priority(priority).label)
