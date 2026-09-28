from django import forms

from apps.hub.forms import BootstrapFormMixin
from apps.users.access import has_permission

from . import selectors
from .models import FINANCIAL_FIELDS, Contract, ContractDocument, ContractStatus
from .services import CONTRACT_FILE_EXTENSIONS, DOCUMENT_EXTENSIONS, allowed_transitions

DATE_WIDGET = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class ContractForm(BootstrapFormMixin, forms.ModelForm):
    SECTIONS = (
        ('Договор', ('company', 'number', 'title', 'description')),
        ('Сроки', ('start_date', 'end_date', 'signed_date')),
        ('Финансовые условия', ('share_percent', 'calculation_base_type',
                                'calculation_base_description', 'payment_terms')),
        ('Обязательства и условия', ('zea_obligations', 'partner_obligations',
                                     'termination_terms', 'additional_terms')),
    )

    class Meta:
        model = Contract
        fields = (
            'company', 'number', 'title', 'description', 'start_date', 'end_date', 'signed_date',
            'share_percent', 'calculation_base_type', 'calculation_base_description', 'payment_terms',
            'zea_obligations', 'partner_obligations', 'termination_terms', 'additional_terms',
        )
        widgets = {
            'start_date': DATE_WIDGET, 'end_date': DATE_WIDGET, 'signed_date': DATE_WIDGET,
            'description': forms.Textarea(attrs={'rows': 2}),
            'share_percent': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'max': '100'}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['company']  # компания договора не меняется
        else:
            self.fields['company'].queryset = selectors.companies_for_new_contract()
        # Без права на финансовые условия поля не выводятся и не принимаются из POST
        if not has_permission(user, 'contracts.view_financial_terms'):
            for name in FINANCIAL_FIELDS:
                self.fields.pop(name, None)

    def sections(self):
        for title, names in self.SECTIONS:
            fields = [self[name] for name in names if name in self.fields]
            if fields:
                yield title, fields


class ContractStatusForm(BootstrapFormMixin, forms.Form):
    to_status = forms.ChoiceField(label='Новый статус')
    comment = forms.CharField(label='Комментарий', required=False, widget=forms.Textarea,
                              help_text='Для расторжения обязательно укажите причину.')

    def __init__(self, *args, contract, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['to_status'].choices = [
            (value, ContractStatus(value).label) for value in allowed_transitions(contract, user)
        ]


def _accept(extensions):
    return ','.join(extensions)


class ContractFileForm(BootstrapFormMixin, forms.Form):
    # FileInput, не ClearableFileInput: у приватного файла нет публичного URL
    file = forms.FileField(label='Подписанный договор (PDF, до 20 МБ)',
                           widget=forms.FileInput(attrs={'accept': _accept(CONTRACT_FILE_EXTENSIONS)}))


class ContractDocumentForm(BootstrapFormMixin, forms.ModelForm):
    upload = forms.FileField(label='Файл (PDF, DOC/DOCX, XLS/XLSX, JPG/PNG — до 20 МБ)',
                             widget=forms.FileInput(attrs={'accept': _accept(DOCUMENT_EXTENSIONS)}))

    class Meta:
        model = ContractDocument
        fields = ('document_type', 'title', 'note')
        widgets = {'note': forms.Textarea(attrs={'rows': 2})}


class ContractFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Поиск', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Номер или компания'}))
    company = forms.ChoiceField(label='Компания', required=False)
    status = forms.ChoiceField(label='Статус', required=False,
                               choices=[('', 'Все статусы')] + list(ContractStatus.choices))
    date_from = forms.DateField(label='Период с', required=False, widget=DATE_WIDGET)
    date_to = forms.DateField(label='по', required=False, widget=DATE_WIDGET)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].choices = [('', 'Все компании')] + [
            (str(c.pk), c.name) for c in selectors.companies_with_contracts()
        ]

    def selector_kwargs(self):
        data = self.cleaned_data if self.is_valid() else {}
        return {
            'search': (data.get('q') or '').strip(),
            'company_id': data.get('company') or None,
            'status': data.get('status') or '',
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
        }
