from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.projects.selectors import user_active_projects

from .models import EmployeeProfile, Specialization


def employee_list(*, search='', specialization_id=None, show_inactive=False):
    qs = (EmployeeProfile.objects.select_related('user')
          .prefetch_related('specializations', 'user__groups'))
    if not show_inactive:
        qs = qs.filter(is_active=True, user__is_active=True)
    if search:
        qs = qs.filter(Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search)
                       | Q(user__username__icontains=search) | Q(position__icontains=search))
    if specialization_id:
        qs = qs.filter(specializations__id=specialization_id)
    return qs.distinct()


def with_workload(employees):
    """Добавляет каждому сотруднику список и число активных проектов.

    MVP: по запросу на сотрудника — команда ZEA небольшая. При росте — агрегировать.
    """
    result = []
    for employee in employees:
        projects = list(user_active_projects(employee.user))
        employee.active_projects = projects
        employee.active_projects_count = len(projects)
        result.append(employee)
    return result


def employee_detail(pk):
    return (EmployeeProfile.objects.select_related('user')
            .prefetch_related('specializations', 'user__groups').get(pk=pk))


def participation_history(user):
    return (user.project_memberships.select_related('project__company', 'specialization')
            .order_by('-is_active', '-joined_at'))


def users_without_profile():
    return (get_user_model().objects.filter(is_active=True, employee__isnull=True)
            .order_by('first_name', 'last_name', 'username'))


def active_specializations():
    return Specialization.objects.filter(is_active=True)
