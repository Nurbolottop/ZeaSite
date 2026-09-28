from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView

from apps.projects import permissions as project_perms
from apps.users.access import get_user_roles, has_permission
from apps.users.mixins import RoleRequiredMixin

from . import selectors, services
from .forms import EmployeeFilterForm, EmployeeForm
from .models import EmployeeProfile


class EmployeeListView(RoleRequiredMixin, ListView):
    module = 'team'
    permission = 'team.view'
    template_name = 'team/employee_list.html'
    context_object_name = 'employees'

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = EmployeeFilterForm(self.request.GET or None)
        return self._filter_form

    def get_queryset(self):
        return selectors.with_workload(selectors.employee_list(**self.get_filter_form().selector_kwargs()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for employee in context['employees']:
            employee.hub_roles = get_user_roles(employee.user)
        context.update({'filter_form': self.get_filter_form(),
                        'querystring': self.request.GET.urlencode(),
                        'can_manage': has_permission(self.request.user, 'team.manage')})
        return context


class EmployeeDetailView(RoleRequiredMixin, DetailView):
    module = 'team'
    permission = 'team.view'
    template_name = 'team/employee_detail.html'
    context_object_name = 'employee'

    def get_object(self, queryset=None):
        try:
            return selectors.employee_detail(self.kwargs['pk'])
        except EmployeeProfile.DoesNotExist:
            raise Http404('Сотрудник не найден')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee, viewer = self.object, self.request.user
        [employee] = selectors.with_workload([employee])
        # название проекта видно всем с доступом к команде (нужно для нагрузки),
        # ссылка — только если проект доступен смотрящему
        projects = [{'project': p, 'linked': project_perms.can_view(viewer, p)}
                    for p in employee.active_projects]
        history = [{'membership': m, 'linked': project_perms.can_view(viewer, m.project)}
                   for m in selectors.participation_history(employee.user)]
        context.update({'hub_roles': get_user_roles(employee.user), 'projects': projects,
                        'history': history,
                        'can_manage': has_permission(viewer, 'team.manage')})
        return context


class EmployeeFormMixin(RoleRequiredMixin):
    module = 'team'
    permission = 'team.manage'
    form_class = EmployeeForm
    template_name = 'team/employee_form.html'

    def form_valid(self, form):
        try:
            profile = services.save_employee(profile=form.save(commit=False),
                                             specializations=form.cleaned_data['specializations'],
                                             user=self.request.user)
        except ValidationError as error:
            if hasattr(error, 'error_dict'):
                for field, errors in error.error_dict.items():
                    form.add_error(field if field in form.fields else None, errors)
            else:
                form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, 'Профиль сотрудника сохранён.')
        return redirect('team:detail', pk=profile.pk)


class EmployeeCreateView(EmployeeFormMixin, FormView):
    pass


class EmployeeUpdateView(EmployeeFormMixin, FormView):
    def get_form_kwargs(self):
        profile = get_object_or_404(EmployeeProfile, pk=self.kwargs['pk'])
        return {**super().get_form_kwargs(), 'instance': profile}
