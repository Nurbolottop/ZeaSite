from django import forms
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from .choices import REQUEST_TYPE_CHOICES, SERVICE_CHOICES
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Заявка с сайта. Тип обращения, направление, компания и сфера пока
    не хранятся отдельными полями (без миграции contacts) — они дописываются
    в начало message на русском, чтобы заявку было удобно читать в админке."""

    request_type = forms.ChoiceField(
        choices=REQUEST_TYPE_CHOICES,
        required=False,
        label=_('Тип обращения'),
        widget=forms.RadioSelect,
    )
    service = forms.ChoiceField(
        choices=[('', _('Выберите направление'))] + SERVICE_CHOICES,
        required=False,
        label=_('Направление'),
    )
    company = forms.CharField(max_length=150, required=False, label=_('Компания'))
    industry = forms.CharField(max_length=150, required=False, label=_('Сфера бизнеса'))

    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'email', 'message']
        labels = {
            'name':    _('Имя'),
            'phone':   _('Телефон / WhatsApp'),
            'email':   _('Email'),
            'message': _('Сообщение'),
        }

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get('phone', '').strip()
        email = cleaned.get('email', '').strip()
        if not phone and not email:
            raise forms.ValidationError(
                _('Укажите телефон или email — чтобы мы могли связаться с вами.')
            )
        return cleaned

    def build_message(self):
        data = self.cleaned_data
        with translation.override('ru'):
            request_type = data.get('request_type') or 'other'
            tags = [str(dict(REQUEST_TYPE_CHOICES)[request_type])]
            if data.get('service'):
                tags.append(str(dict(SERVICE_CHOICES)[data['service']]))
        lines = [' '.join(f'[{tag}]' for tag in tags)]
        if data.get('company'):
            lines.append(f'Компания: {data["company"].strip()}')
        if data.get('industry'):
            lines.append(f'Сфера: {data["industry"].strip()}')
        return '\n'.join(lines) + '\n\n' + data['message']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.source = 'form'
        instance.message = self.build_message()
        if commit:
            instance.save()
        return instance
