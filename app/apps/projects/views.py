from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from apps.contracts.models import Contract, ContractStatus
from apps.users.access import has_permission, has_role
from apps.users.mixins import RoleRequiredMixin
from apps.users.roles import Role

from . import permissions as perms
from . import selectors, services
from .forms import MemberForm, ProjectFilterForm, ProjectForm, ProjectStatusForm, TechnicalInfoForm
from .models import Project, ProjectMember, ProjectTechnicalInfo


def _apply_service_errors(form, error):
    if hasattr(error, 'error_dict'):
        for field, errors in error.error_dict.items():
            form.add_error(field if field in form.fields else None, errors)
    else:
        form.add_error(None, error)


def marketing_only(user):
    """Видит проекты только через роль «Маркетинг» → сокращённый список."""
    return has_role(user, Role.MARKETING) and not has_role(
        user, Role.HEAD, Role.BIZDEV, Role.PM, Role.TECH_LEAD, Role.DEVOPS)


class ProjectListView(RoleRequiredMixin, ListView):
    module = 'projects'
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = ProjectFilterForm(self.request.GET or None, user=self.request.user)
        return self._filter_form

    def get_queryset(self):
        return selectors.project_list(self.request.user, **self.get_filter_form().selector_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop('page', None)
        user = self.request.user
        context.update({
            'filter_form': self.get_filter_form(),
            'querystring': query.urlencode(),
            'can_create': perms.can_create(user),
            'limited': marketing_only(user),
            'sees_all': has_permission(user, 'projects.view_all'),
        })
        return context


class ProjectDetailView(RoleRequiredMixin, DetailView):
    module = 'projects'
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_object(self, queryset=None):
        try:
            project = selectors.project_detail(self.kwargs['pk'])
        except Project.DoesNotExist:
            raise Http404('Проект не найден')
        if not perms.can_view(self.request.user, project):
            raise Http404('Проект не найден')
        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project, user = self.object, self.request.user
        limited = perms.is_limited(user, project)
        scope = perms.member_scope(user, project)
        members = [m for m in project.members.all()]
        context.update({
            'limited': limited,
            'active_members': [m for m in members if m.is_active],
            'former_members': [m for m in members if not m.is_active],
            'history': project.status_history.all(),
            'tech': ProjectTechnicalInfo.objects.filter(project=project).first(),
            'can_edit': perms.can_edit_work(user, project),
            'status_targets': services.allowed_transitions(project, user),
            'can_view_team': perms.can_view_team(user, project),
            'can_view_notes': perms.can_view_notes(user, project),
            'can_view_technical': perms.can_view_technical(user, project),
            'can_edit_technical': perms.can_edit_technical(user, project),
            'member_scope': scope,
            'can_open_company': has_permission(user, 'partners.view'),
            'can_open_contract': has_permission(user, 'contracts.view'),
        })
        return context


class ProjectCreateView(RoleRequiredMixin, FormView):
    module = 'projects'
    permission = 'projects.manage_all'
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.request.user}

    def get_initial(self):
        initial = super().get_initial()
        company_id = self.request.GET.get('company', '')
        if company_id.isdigit():
            contract = Contract.objects.filter(company_id=company_id, status=ContractStatus.ACTIVE).first()
            if contract:
                initial['contract'] = contract.pk
        return initial

    def form_valid(self, form):
        try:
            project = services.create_project(project=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        messages.success(self.request, f'Проект {project.code} создан.')
        return redirect(project.get_absolute_url())


class ProjectObjectMixin(RoleRequiredMixin):
    """Действие над проектом: невидимый проект → 404, видимый без права → 403."""

    module = 'projects'
    template_name = 'projects/project_action_form.html'
    title = ''
    submit_label = 'Сохранить'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not self.has_access(request.user):
            return self.handle_no_permission()
        self.project = get_object_or_404(Project.objects.select_related('company', 'contract'), pk=kwargs['pk'])
        if not perms.can_view(request.user, self.project):
            raise Http404('Проект не найден')
        if not self.allowed(request.user, self.project):
            raise PermissionDenied('Нет права на это действие с проектом.')
        return super().dispatch(request, *args, **kwargs)

    def allowed(self, user, project):
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'project': self.project, 'title': self.title, 'submit_label': self.submit_label})
        return context

    def done(self, message):
        messages.success(self.request, message)
        return redirect(self.project.get_absolute_url())


class ProjectUpdateView(ProjectObjectMixin, FormView):
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def allowed(self, user, project):
        return perms.can_edit_work(user, project)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'instance': self.project, 'user': self.request.user}

    def form_valid(self, form):
        try:
            services.update_project(project=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done('Проект сохранён.')


class ProjectStatusView(ProjectObjectMixin, FormView):
    form_class = ProjectStatusForm
    title = 'Изменить статус проекта'
    submit_label = 'Изменить статус'

    def allowed(self, user, project):
        return perms.can_change_status(user, project)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'project': self.project, 'user': self.request.user}

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        try:
            # в сервис уходит значение из POST как есть: он сам проверит право и переход
            record = services.change_project_status(project=self.project, user=request.user,
                                                    to_status=request.POST.get('to_status', ''),
                                                    comment=request.POST.get('comment', ''))
        except ValidationError as error:
            form.is_valid()
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done(f'Статус проекта: {record.get_to_status_display()}.')


class TechnicalInfoView(ProjectObjectMixin, FormView):
    form_class = TechnicalInfoForm
    template_name = 'projects/technical_form.html'
    title = 'Техническая информация'

    def allowed(self, user, project):
        return perms.can_edit_technical(user, project)

    def get_form_kwargs(self):
        info = (ProjectTechnicalInfo.objects.filter(project=self.project).first()
                or ProjectTechnicalInfo(project=self.project))
        return {**super().get_form_kwargs(), 'instance': info}

    def form_valid(self, form):
        try:
            services.save_technical_info(info=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done('Техническая информация сохранена.')


class MemberAddView(ProjectObjectMixin, FormView):
    form_class = MemberForm
    title = 'Добавить участника'
    submit_label = 'Добавить в команду'

    def allowed(self, user, project):
        return perms.member_scope(user, project) is not None

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(),
                'scope': perms.member_scope(self.request.user, self.project)}

    def form_valid(self, form):
        try:
            services.add_member(project=self.project, user=self.request.user, **form.cleaned_data)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done('Участник добавлен в команду проекта.')


class MemberRemoveView(ProjectObjectMixin, View):
    def allowed(self, user, project):
        return perms.member_scope(user, project) is not None

    def post(self, request, *args, **kwargs):
        membership = get_object_or_404(ProjectMember, pk=kwargs['member_pk'], project=self.project)
        try:
            services.remove_member(membership=membership, user=request.user)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
            return redirect(self.project.get_absolute_url())
        return self.done(f'{membership.member.get_full_name() or membership.member} выведен(а) из команды проекта.')
