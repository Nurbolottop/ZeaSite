from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView

from apps.users.access import has_permission
from apps.users.mixins import RoleRequiredMixin

from . import selectors, services
from .forms import (
    AssessmentForm, CompanyFilterForm, CompanyForm, ContactForm, DecisionForm, StatusChangeForm,
)
from .models import CandidateAssessment, Company, CompanyContact, CompanyStatus


def _apply_service_errors(form, error):
    """ValidationError из services → ошибки формы (по полям, если они есть в форме)."""
    if hasattr(error, 'error_dict'):
        for field, errors in error.error_dict.items():
            form.add_error(field if field in form.fields else None, errors)
    else:
        form.add_error(None, error)


# ── Списки ────────────────────────────────────────────────────────────────

class CompanyListView(RoleRequiredMixin, ListView):
    template_name = 'partners/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    with_status_filter = True

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = CompanyFilterForm(self.request.GET or None,
                                                  with_status=self.with_status_filter)
        return self._filter_form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop('page', None)
        context.update({
            'filter_form': self.get_filter_form(),
            'querystring': query.urlencode(),
            'section': self.module,
            'can_edit': has_permission(self.request.user, 'partners.edit'),
        })
        return context


class CandidateListView(CompanyListView):
    module = 'candidates'

    def get_queryset(self):
        return selectors.candidate_list(**self.get_filter_form().selector_kwargs())


class PartnerListView(CompanyListView):
    module = 'partners'
    with_status_filter = False

    def get_queryset(self):
        return selectors.partner_list(**self.get_filter_form().selector_kwargs())


# ── Карточка ──────────────────────────────────────────────────────────────

class CompanyDetailView(RoleRequiredMixin, DetailView):
    template_name = 'partners/company_detail.html'
    context_object_name = 'company'

    def get_object(self, queryset=None):
        try:
            return selectors.company_detail(self.kwargs['pk'])
        except Company.DoesNotExist:
            raise Http404('Компания не найдена')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Партнёр открывается в разделе «Партнёры», кандидат — в «Кандидатах»
        canonical = self.object.get_absolute_url()
        if request.path != canonical:
            return redirect(canonical)
        request.hub_active_module = 'partners' if self.object.is_partner else 'candidates'
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object
        user = self.request.user
        context.update({
            'assessment': getattr(company, 'assessment', None),
            'contacts': company.contacts.all(),
            'history': company.status_history.all(),
            'decisions': company.decisions.all(),
            'can_edit': has_permission(user, 'partners.edit'),
            'can_decide': (has_permission(user, 'partners.decide')
                           and company.status in services.DECISION_STATUSES),
            'status_targets': services.allowed_transitions(company),
            'funnel': _funnel(company),
        })
        return context


def _funnel(company):
    """Шаги воронки для прогресс-бара карточки."""
    steps = [s for s in CompanyStatus if s != CompanyStatus.REJECTED]
    current = steps.index(company.status) if company.status in steps else -1
    return [{'label': s.label, 'done': i < current, 'current': i == current}
            for i, s in enumerate(steps)]


# ── Действия с компанией ─────────────────────────────────────────────────

class CompanyActionMixin(RoleRequiredMixin):
    """Действие над существующей компанией: грузит company, подсвечивает раздел меню."""

    module = 'candidates'
    permission = 'partners.edit'
    template_name = 'partners/company_action_form.html'
    title = ''
    submit_label = 'Сохранить'
    success_message = ''

    def dispatch(self, request, *args, **kwargs):
        # Сначала права, потом объект: без доступа — 403, не 404 (не раскрываем id)
        if not request.user.is_authenticated or not self.has_access(request.user):
            return self.handle_no_permission()
        self.company = get_object_or_404(Company, pk=kwargs['pk'])
        request.hub_active_module = 'partners' if self.company.is_partner else 'candidates'
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'company': self.company, 'title': self.title,
                        'submit_label': self.submit_label})
        return context

    def get_success_url(self):
        return self.company.get_absolute_url()

    def done(self):
        if self.success_message:
            messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())


class CompanyCreateView(RoleRequiredMixin, FormView):
    module = 'candidates'
    permission = 'partners.edit'
    form_class = CompanyForm
    template_name = 'partners/company_form.html'

    def get_initial(self):
        initial = super().get_initial()
        # Менеджер по развитию по умолчанию отвечает за добавленного им кандидата
        if selectors.manager_choices().filter(pk=self.request.user.pk).exists():
            initial['manager'] = self.request.user.pk
        return initial

    def form_valid(self, form):
        try:
            company = services.create_company(company=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        messages.success(self.request, f'Кандидат «{company}» добавлен.')
        return redirect(company.get_absolute_url())


class CompanyUpdateView(CompanyActionMixin, FormView):
    form_class = CompanyForm
    template_name = 'partners/company_form.html'
    success_message = 'Данные компании сохранены.'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'instance': self.company}

    def form_valid(self, form):
        try:
            services.update_company(company=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done()


class StatusChangeView(CompanyActionMixin, FormView):
    form_class = StatusChangeForm
    title = 'Изменить статус'
    submit_label = 'Изменить статус'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'company': self.company}

    def form_valid(self, form):
        try:
            record = services.change_status(company=self.company, user=self.request.user,
                                            to_status=form.cleaned_data['to_status'],
                                            comment=form.cleaned_data['comment'])
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        self.success_message = f'Статус изменён: {record.get_to_status_display()}.'
        return self.done()


class DecisionCreateView(CompanyActionMixin, FormView):
    permission = 'partners.decide'
    form_class = DecisionForm
    title = 'Решение команды'
    submit_label = 'Зафиксировать решение'

    def form_valid(self, form):
        try:
            record = services.make_decision(company=self.company, user=self.request.user,
                                            decision=form.cleaned_data['decision'],
                                            comment=form.cleaned_data['comment'],
                                            review_date=form.cleaned_data['review_date'])
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        self.success_message = f'Решение зафиксировано: {record.get_decision_display()}.'
        return self.done()


class AssessmentUpdateView(CompanyActionMixin, FormView):
    form_class = AssessmentForm
    template_name = 'partners/assessment_form.html'
    title = 'Анализ кандидата'
    success_message = 'Анализ сохранён.'

    def get_form_kwargs(self):
        instance = (CandidateAssessment.objects.filter(company=self.company).first()
                    or CandidateAssessment(company=self.company))
        return {**super().get_form_kwargs(), 'instance': instance}

    def form_valid(self, form):
        services.save_assessment(assessment=form.save(commit=False), user=self.request.user)
        return self.done()


class ContactCreateView(CompanyActionMixin, FormView):
    form_class = ContactForm
    title = 'Новый контакт'
    submit_label = 'Добавить контакт'
    success_message = 'Контакт добавлен.'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'instance': CompanyContact(company=self.company)}

    def form_valid(self, form):
        services.save_contact(contact=form.save(commit=False))
        return self.done()


class ContactUpdateView(ContactCreateView):
    title = 'Редактировать контакт'
    submit_label = 'Сохранить'
    success_message = 'Контакт сохранён.'

    def get_form_kwargs(self):
        contact = get_object_or_404(CompanyContact, pk=self.kwargs['contact_pk'], company=self.company)
        return {**FormView.get_form_kwargs(self), 'instance': contact}


class ContactDeleteView(CompanyActionMixin, TemplateView):
    template_name = 'partners/contact_confirm_delete.html'
    title = 'Удалить контакт'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = self.get_contact()
        return context

    def get_contact(self):
        return get_object_or_404(CompanyContact, pk=self.kwargs['contact_pk'], company=self.company)

    def post(self, request, *args, **kwargs):
        services.delete_contact(contact=self.get_contact())
        self.success_message = 'Контакт удалён.'
        return self.done()
