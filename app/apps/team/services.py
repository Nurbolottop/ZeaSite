from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.users.access import has_permission

from .models import EmployeeProfile


@transaction.atomic
def save_employee(*, profile: EmployeeProfile, specializations, user) -> EmployeeProfile:
    """Создание / изменение профиля сотрудника (только Руководитель)."""
    if not has_permission(user, 'team.manage'):
        raise PermissionDenied('Управлять командой может только Руководитель.')
    if profile.pk is None and EmployeeProfile.objects.filter(user_id=profile.user_id).exists():
        raise ValidationError({'user': 'У пользователя уже есть профиль сотрудника.'})
    profile.full_clean()
    profile.save()
    profile.specializations.set(specializations)
    return profile
