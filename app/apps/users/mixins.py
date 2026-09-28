from django.contrib.auth.mixins import LoginRequiredMixin

from .access import can_access_module, has_permission, has_role

DENIED_MESSAGE = 'У вас нет доступа к этому разделу. Обратитесь к руководителю, чтобы получить нужную роль.'


class RoleRequiredMixin(LoginRequiredMixin):
    """Доступ к view по модулю или по явному списку ролей.

        class CandidateListView(RoleRequiredMixin, ListView):
            module = 'candidates'              # роли берутся из MODULE_ACCESS

        class CompanyUpdateView(RoleRequiredMixin, UpdateView):
            module = 'candidates'
            permission = 'partners.edit'       # действие из PERMISSIONS

        class SalaryView(RoleRequiredMixin, TemplateView):
            allowed_roles = (Role.HEAD,)       # точечное ограничение

    Неавторизованный → редирект на login, авторизованный без прав → 403.
    Superuser проходит всегда.
    """

    module = None
    permission = None
    allowed_roles = None
    permission_denied_message = DENIED_MESSAGE

    def has_access(self, user):
        if self.module is not None and not can_access_module(user, self.module):
            return False
        if self.permission is not None and not has_permission(user, self.permission):
            return False
        if self.allowed_roles is not None and not has_role(user, *self.allowed_roles):
            return False
        return True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not self.has_access(request.user):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ScopedQuerysetMixin:
    """Ограничение queryset по пользователю для List/Detail/Update view.

    Модуль переопределяет scope_queryset() (обычно вызывая selector),
    например PM видит только свои проекты. Superuser видит всё.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return qs
        return self.scope_queryset(qs, user)

    def scope_queryset(self, qs, user):
        return qs
