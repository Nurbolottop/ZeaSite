from django import forms

from apps.hub.forms import BootstrapFormMixin
from apps.users.profile import display_name

from . import selectors
from .models import EmployeeProfile


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{display_name(obj)} ({obj.username})'


class EmployeeForm(BootstrapFormMixin, forms.ModelForm):
    user = UserChoiceField(queryset=None, label='Пользователь Hub',
                           help_text='Учётную запись создаёт администратор. Роли доступа назначаются там же.')

    class Meta:
        model = EmployeeProfile
        fields = ('user', 'position', 'employment_type', 'specializations', 'started_at', 'is_active', 'note')
        widgets = {'specializations': forms.CheckboxSelectMultiple,
                   'started_at': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                   'note': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['user']
        else:
            self.fields['user'].queryset = selectors.users_without_profile()
        self.fields['specializations'].queryset = selectors.active_specializations()


class EmployeeFilterForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(label='Поиск', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Имя или должность'}))
    specialization = forms.ModelChoiceField(label='Специализация', required=False, queryset=None,
                                            empty_label='Все специализации')
    inactive = forms.BooleanField(label='Показать неактивных', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialization'].queryset = selectors.active_specializations()

    def selector_kwargs(self):
        data = self.cleaned_data if self.is_valid() else {}
        spec = data.get('specialization')
        return {'search': (data.get('q') or '').strip(),
                'specialization_id': spec.pk if spec else None,
                'show_inactive': bool(data.get('inactive'))}
