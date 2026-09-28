from django import template

from apps.users import profile

register = template.Library()


@register.filter
def display_name(user):
    return profile.display_name(user)


@register.filter
def initials(user):
    return profile.initials(user)
