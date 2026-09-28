from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.contracts.models import Contract
from apps.hub.forms import BootstrapFormMixin
from apps.team.models import Specialization
from apps.users.profile import display_name

from . import permissions as perms
from . import selectors
from .models import Priority, Project, ProjectStatus, ProjectTechnicalInfo, ProjectType
from .services import allowed_transitions, eligible_members

DATE_WIDGET = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return display_name(obj)


class ContractChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.company.name} — договор № {obj.number}'


class ProjectForm(BootstrapFormMixin, forms.ModelForm):
    SECTIONS = (
        ('Проект', ('contract', 'name', 'code', 'project_type', 'project_type_other', 'description')),
        ('Ответственные', ('pm', 'technical_lead')),
        ('Сроки и приоритет', ('priority', 'start_date', 'planned_end_date', 'actual_end_date')),
        ('Заметки', ('notes',)),
    )
    CORE = ('contract', 'name', 'code', 'pm', 'technical_lead')

    contract = ContractChoiceField(queryset=None, label='Договор',
                                   help_text='Действующий договор партнёра. Компания проекта берётся из договора.')
    pm = UserChoiceField(queryset=None, label='PM', help_text='Только пользователи с ролью «Проектный менеджер (PM)».')
    technical_lead = UserChoiceField(queryset=None, label='Технический руководитель',
                                     help_text='Только пользователи с ролью «Технический руководитель».')

    class Meta:
        model = Project
        fields = ('contract', 'name', 'code', 'project_type', 'project_type_other', 'description',
                  'pm', 'technical_lead', 'priority', 'start_date', 'planned_end_date',
                  'actual_end_date', 'notes')
        widgets = {'start_date': DATE_WIDGET, 'planned_end_date': DATE_WIDGET,
                   'actual_end_date': DATE_WIDGET, 'description': forms.Textarea(attrs={'rows': 3}),
                   'notes': forms.Textarea(attrs={'rows': 4}),
                   'code': forms.TextInput(attrs={'placeholder': 'KE-CRM'})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        instance = self.instance
        contracts = selectors.active_contracts_for_projects()
        pms, leads = selectors.pm_choices(), selectors.tech_lead_choices()
        if instance.pk:
            # текущие значения остаются в списках, даже если договор истёк / роль снята
            contracts = Contract.objects.filter(
                Q(pk__in=contracts.values('pk')) | Q(pk=instance.contract_id)).select_related('company')
            pms = User.objects.filter(Q(pk__in=pms.values('pk')) | Q(pk=instance.pm_id))
            leads = User.objects.filter(Q(pk__in=leads.values('pk')) | Q(pk=instance.technical_lead_id))
        self.fields['contract'].queryset = contracts
        self.fields['pm'].queryset = pms
        self.fields['technical_lead'].queryset = leads
        if instance.pk and not perms.can_edit_core(user):
            for name in self.CORE:  # PM не меняет компанию, договор, PM и тех. руководителя
                del self.fields[name]

    def sections(self):
        for title, names in self.SECTIONS:
            fields = [self[n] for n in names if n in self.fields]
            if fields:
                yield title, fields


class ProjectStatusForm(BootstrapFormMixin, forms.Form):
    to_status = forms.ChoiceField(label='Новый статус')
    comment = forms.CharField(label='Комментарий', required=False, widget=forms.Textarea,
                              help_text='Для приостановки и отмены причина обязательна.')

    def __init__(self, *args, project, user, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for value in allowed_transitions(project, user):
            label = ProjectStatus(value).label
            if project.status == ProjectStatus.PAUSED and value != ProjectStatus.CANCELLED:
                label = f'Возобновить — {label}'
            choices.append((value, label))
        self.fields['to_status'].choices = choices


class TechnicalInfoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectTechnicalInfo
        fields = ProjectTechnicalInfo.TEXT_FIELDS
        widgets = {
            'repository_url': forms.URLInput(attrs={'placeholder': 'https://github.com/zea/…'}),
            'production_url': forms.URLInput(attrs={'placeholder': 'https://'}),
            'staging_url': forms.URLInput(attrs={'placeholder': 'https://'}),
            'technology_stack': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Django, PostgreSQL, React…'}),
        }


class MemberForm(BootstrapFormMixin, forms.Form):
    member = UserChoiceField(queryset=None, label='Сотрудник')
    specialization = forms.ModelChoiceField(queryset=None, label='Роль в проекте')
    note = forms.CharField(label='Заметка', required=False, max_length=255)

    def __init__(self, *args, scope, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = eligible_members()
        specs = Specialization.objects.filter(is_active=True)
        if scope == 'technical':
            specs = specs.filter(is_technical=True)
        self.fields['specialization'].queryset = specs


class ProjectFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Поиск', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Проект, код или компания'}))
    company = forms.ChoiceField(label='Компания', required=False)
    status = forms.ChoiceField(label='Статус', required=False, choices=(
        [('', 'Все'), ('active', 'Активные'), ('overdue', 'Просроченные')] + list(ProjectStatus.choices)))
    type = forms.ChoiceField(label='Тип', required=False, choices=[('', 'Все типы')] + list(ProjectType.choices))
    pm = forms.ChoiceField(label='PM', required=False)
    lead = forms.ChoiceField(label='Тех. руководитель', required=False)
    priority = forms.ChoiceField(label='Приоритет', required=False,
                                 choices=[('', 'Любой')] + list(Priority.choices))
    sort = forms.ChoiceField(label='Сортировка', required=False, choices=(
        ('priority', 'По приоритету'), ('deadline', 'По сроку'), ('-updated', 'Недавно изменённые'),
        ('status', 'По этапу'), ('name', 'По названию'), ('-created', 'Сначала новые')))

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].choices = [('', 'Все компании')] + [
            (str(c.pk), c.name) for c in selectors.companies_with_projects(user)]
        self.fields['pm'].choices = [('', 'Все')] + [(str(u.pk), display_name(u)) for u in selectors.pm_choices()]
        self.fields['lead'].choices = [('', 'Все')] + [
            (str(u.pk), display_name(u)) for u in selectors.tech_lead_choices()]

    def selector_kwargs(self):
        data = self.cleaned_data if self.is_valid() else {}
        return {
            'search': (data.get('q') or '').strip(),
            'company_id': data.get('company') or None,
            'status': data.get('status') or '',
            'project_type': data.get('type') or '',
            'pm_id': data.get('pm') or None,
            'technical_lead_id': data.get('lead') or None,
            'priority': data.get('priority') or '',
            'sort': data.get('sort') or selectors.DEFAULT_SORT,
        }
