"""Вспомогательные функции для отображения сотрудника Hub."""
from django.core.exceptions import ObjectDoesNotExist


def get_hub_profile(user):
    """HubProfile пользователя или None, если профиль ещё не заполнен."""
    if not user.is_authenticated:
        return None
    try:
        return user.hub_profile
    except ObjectDoesNotExist:
        return None


def display_name(user):
    return user.get_full_name() or user.get_username()


def initials(user):
    parts = [p for p in (user.first_name, user.last_name) if p]
    if parts:
        return ''.join(p[0] for p in parts).upper()
    return user.get_username()[:2].upper()
