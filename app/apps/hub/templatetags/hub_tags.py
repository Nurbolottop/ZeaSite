from django import template

from apps.users import profile
from apps.users.access import has_permission

register = template.Library()


@register.filter
def display_name(user):
    return profile.display_name(user)


@register.filter
def initials(user):
    return profile.initials(user)


@register.filter
def can(user, permission):
    """{% if user|can:'partners.edit' %} — проверка права из PERMISSIONS."""
    return has_permission(user, permission)
