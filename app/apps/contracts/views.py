from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from apps.users.access import has_permission
from apps.users.mixins import RoleRequiredMixin

from . import selectors, services
from .forms import (
    ContractDocumentForm, ContractFileForm, ContractFilterForm, ContractForm, ContractStatusForm,
)
from .models import Contract, ContractDocument


def _apply_service_errors(form, error):
    if hasattr(error, 'error_dict'):
        for field, errors in error.error_dict.items():
            form.add_error(field if field in form.fields else None, errors)
    else:
        form.add_error(None, error)


def _private_file_response(field_file, display_name):
    """Отдача приватного файла: только вложением, без выполнения в браузере."""
    try:
        handle = field_file.open('rb')
    except (FileNotFoundError, ValueError):
        raise Http404('Файл не найден')
    response = FileResponse(handle, as_attachment=True,
                            filename=services.safe_display_name(display_name),
                            content_type=services.content_type_for(field_file.name))
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "default-src 'none'; sandbox"
    response['Cache-Control'] = 'private, no-store'
    return response


class ContractListView(RoleRequiredMixin, ListView):
    module = 'contracts'
    permission = 'contracts.view'
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 20

    def get_filter_form(self):
        if not hasattr(self, '_filter_form'):
            self._filter_form = ContractFilterForm(self.request.GET or None)
        return self._filter_form

    def get_queryset(self):
        return selectors.contract_list(**self.get_filter_form().selector_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.copy()
        query.pop('page', None)
        user = self.request.user
        context.update({
            'filter_form': self.get_filter_form(),
            'querystring': query.urlencode(),
            'can_manage': has_permission(user, 'contracts.manage'),
            'show_financial': has_permission(user, 'contracts.view_financial_terms'),
        })
        return context


class ContractDetailView(RoleRequiredMixin, DetailView):
    module = 'contracts'
    permission = 'contracts.view'
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'

    def get_object(self, queryset=None):
        try:
            return selectors.contract_detail(self.kwargs['pk'])
        except Contract.DoesNotExist:
            raise Http404('Договор не найден')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract, user = self.object, self.request.user
        show_financial = has_permission(user, 'contracts.view_financial_terms')
        documents = [d for d in contract.documents.all() if show_financial or not d.is_financial]
        can_manage = has_permission(user, 'contracts.manage')
        context.update({
            'show_financial': show_financial,
            'documents': documents,
            'hidden_documents': len(contract.documents.all()) - len(documents),
            'history': contract.status_history.all(),
            'can_manage': can_manage,
            'can_edit_terms': can_manage and contract.status in services.EDITABLE_STATUSES,
            'status_targets': services.allowed_transitions(contract, user),
            'missing_for_active': services.readiness_errors(contract, 'active'),
        })
        return context


class ContractCreateView(RoleRequiredMixin, FormView):
    module = 'contracts'
    permission = 'contracts.manage'
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.request.user}

    def get_initial(self):
        initial = super().get_initial()
        company_id = self.request.GET.get('company')
        if company_id and company_id.isdigit():
            initial['company'] = int(company_id)
        return initial

    def form_valid(self, form):
        try:
            contract = services.create_contract(contract=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        messages.success(self.request, f'Договор № {contract.number} создан (черновик).')
        return redirect(contract.get_absolute_url())


class ContractActionMixin(RoleRequiredMixin):
    module = 'contracts'
    permission = 'contracts.manage'
    template_name = 'contracts/contract_action_form.html'
    title = ''
    submit_label = 'Сохранить'

    def dispatch(self, request, *args, **kwargs):
        # Сначала права, потом объект — без доступа 403, id не раскрываются
        if not request.user.is_authenticated or not self.has_access(request.user):
            return self.handle_no_permission()
        self.contract = get_object_or_404(Contract.objects.select_related('company'), pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'contract': self.contract, 'title': self.title,
                        'submit_label': self.submit_label})
        return context

    def done(self, message):
        messages.success(self.request, message)
        return redirect(self.contract.get_absolute_url())


class ContractUpdateView(ContractActionMixin, FormView):
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'instance': self.contract, 'user': self.request.user}

    def form_valid(self, form):
        try:
            services.update_contract(contract=form.save(commit=False), user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done('Договор сохранён.')


class ContractStatusView(ContractActionMixin, FormView):
    form_class = ContractStatusForm
    title = 'Изменить статус договора'
    submit_label = 'Изменить статус'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'contract': self.contract, 'user': self.request.user}

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        # Недоступный статус в форме → всё равно передаём в сервис: он вернёт 403/ошибку,
        # а не молча проигнорирует попытку (например, активацию менеджером)
        to_status = request.POST.get('to_status', '')
        comment = request.POST.get('comment', '')
        try:
            record = services.change_contract_status(contract=self.contract, to_status=to_status,
                                                     user=request.user, comment=comment)
        except ValidationError as error:
            form.is_valid()
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done(f'Статус договора: {record.get_to_status_display()}.')


class ContractFileUploadView(ContractActionMixin, FormView):
    form_class = ContractFileForm
    title = 'Файл подписанного договора'
    submit_label = 'Загрузить'

    def form_valid(self, form):
        try:
            services.upload_contract_file(contract=self.contract, uploaded=form.cleaned_data['file'],
                                          user=self.request.user)
        except ValidationError as error:
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done('Файл договора загружен.')


class ContractDocumentCreateView(ContractActionMixin, FormView):
    form_class = ContractDocumentForm
    title = 'Добавить документ'
    submit_label = 'Загрузить документ'

    def form_valid(self, form):
        document = form.save(commit=False)
        document.contract = self.contract
        try:
            services.add_document(document=document, uploaded=form.cleaned_data['upload'],
                                  user=self.request.user)
        except ValidationError as error:
            if hasattr(error, 'error_dict') and 'file' in error.error_dict:
                error = ValidationError({'upload': error.error_dict['file']})
            _apply_service_errors(form, error)
            return self.form_invalid(form)
        return self.done(f'Документ «{document.title}» загружен.')


class ContractFileDownloadView(RoleRequiredMixin, View):
    """Основной файл: содержит финансовые условия → нужен view_financial_terms."""
    module = 'contracts'
    permission = 'contracts.view_financial_terms'

    def get(self, request, pk):
        contract = get_object_or_404(Contract, pk=pk)
        if not contract.file:
            raise Http404('Файл не загружен')
        return _private_file_response(contract.file, contract.file_original_name or f'contract-{contract.number}.pdf')


class ContractDocumentDownloadView(RoleRequiredMixin, View):
    module = 'contracts'
    permission = 'contracts.view'

    def get(self, request, uid):
        document = get_object_or_404(ContractDocument, uid=uid)
        if document.is_financial and not has_permission(request.user, 'contracts.view_financial_terms'):
            raise PermissionDenied('Документ содержит финансовые условия.')
        return _private_file_response(document.file, document.original_name)

