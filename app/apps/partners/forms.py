from django import forms
from django.utils import timezone

from apps.hub.forms import BootstrapFormMixin
from apps.users.profile import display_name

from . import selectors
from .models import (
    CandidateAssessment, Company, CompanyContact, CompanyStatus, CompanyType, DecisionResult,
)
from .services import allowed_transitions


class ManagerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return display_name(obj)


class CompanyForm(BootstrapFormMixin, forms.ModelForm):
    manager = ManagerChoiceField(queryset=None, required=False, label='Ответственный менеджер',
                                 empty_label='— не назначен —')

    class Meta:
        model = Company
        fields = (
            'name', 'legal_name', 'company_type', 'industry', 'description',
            'website', 'instagram', 'phone', 'email', 'address', 'city',
            'source', 'source_details', 'manager', 'notes',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'website': forms.URLInput(attrs={'placeholder': 'https://'}),
            'instagram': forms.TextInput(attrs={'placeholder': '@company'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = selectors.manager_choices()


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = ('name', 'position', 'phone', 'email', 'telegram', 'is_primary', 'note')
        widgets = {
            'telegram': forms.TextInput(attrs={'placeholder': '@username'}),
            'note': forms.Textarea(attrs={'rows': 2}),
        }


class AssessmentForm(BootstrapFormMixin, forms.ModelForm):
    SECTIONS = (
        ('Бизнес', ('business_model', 'products', 'target_audience', 'team_info',
                    'market_analysis', 'development_plan')),
        ('IT', ('it_state', 'problem', 'proposed_solution', 'mvp_state')),
        ('Финансы', ('revenue', 'financial_indicator', 'financial_transparency')),
        ('Риски', ('legal_risks', 'reputation', 'risks_for_zea')),
        ('Итог', ('manager_comment',)),
    )

    class Meta:
        model = CandidateAssessment
        exclude = ('company', 'created_by', 'updated_by')

    def sections(self):
        for title, names in self.SECTIONS:
            yield title, [self[name] for name in names]


class StatusChangeForm(BootstrapFormMixin, forms.Form):
    to_status = forms.ChoiceField(label='Новый статус')
    comment = forms.CharField(label='Комментарий', required=False, widget=forms.Textarea,
                              help_text='Для отклонения обязательно укажите причину.')

    def __init__(self, *args, company, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['to_status'].choices = [
            (value, CompanyStatus(value).label) for value in allowed_transitions(company)
        ]


class DecisionForm(BootstrapFormMixin, forms.Form):
    review_date = forms.DateField(label='Дата рассмотрения', initial=timezone.localdate,
                                  widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    decision = forms.ChoiceField(label='Решение', choices=DecisionResult.choices)
    comment = forms.CharField(label='Комментарий', required=False, widget=forms.Textarea,
                              help_text='При отклонении обязателен.')


class CompanyFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Поиск', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Название компании'}))
    status = forms.ChoiceField(label='Статус', required=False)
    type = forms.ChoiceField(label='Тип', required=False,
                             choices=[('', 'Все типы')] + list(CompanyType.choices))
    manager = forms.ChoiceField(label='Ответственный', required=False)
    sort = forms.ChoiceField(label='Сортировка', required=False, choices=(
        ('-updated', 'Недавно изменённые'),
        ('-created', 'Сначала новые'),
        ('created', 'Сначала старые'),
        ('name', 'Название А→Я'),
        ('-name', 'Название Я→А'),
        ('status', 'По стадии воронки'),
        ('-status', 'По стадии (обратно)'),
    ))

    def __init__(self, *args, with_status=True, **kwargs):
        super().__init__(*args, **kwargs)
        if with_status:
            self.fields['status'].choices = selectors.candidate_status_filter_choices()
        else:
            del self.fields['status']
        self.fields['manager'].choices = (
            [('', 'Все'), ('none', '— не назначен —')]
            + [(str(u.pk), display_name(u)) for u in selectors.manager_choices()]
        )

    def selector_kwargs(self):
        data = self.cleaned_data if self.is_valid() else {}
        kwargs = {
            'search': (data.get('q') or '').strip(),
            'company_type': data.get('type') or '',
            'manager_id': data.get('manager') or None,
            'sort': data.get('sort') or selectors.DEFAULT_SORT,
        }
        if 'status' in self.fields:
            kwargs['status'] = data.get('status') or ''
        return kwargs
