from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ContactMessage


SERVICE_CHOICES = [
    ('', _('Выберите услугу')),
    ('website',  _('Разработка сайта')),
    ('crm',      _('CRM-система')),
    ('bot',      _('Telegram-бот')),
    ('design',   _('UI/UX Дизайн')),
    ('backend',  _('Backend-разработка')),
    ('other',    _('Другое')),
]


class ContactForm(forms.ModelForm):
    service = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        required=False,
        label=_('Тип услуги'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'phone', 'email', 'message']
        labels = {
            'name':    _('Имя'),
            'phone':   _('Телефон / WhatsApp'),
            'email':   _('Email'),
            'message': _('Сообщение'),
        }
        widgets = {
            'name':    forms.TextInput(attrs={'placeholder': _('Ваше имя')}),
            'phone':   forms.TextInput(attrs={'placeholder': '+996 XXX XXX XXX'}),
            'email':   forms.EmailInput(attrs={'placeholder': 'hello@example.com'}),
            'message': forms.Textarea(attrs={
                'placeholder': _('Опишите вашу задачу...'),
                'rows': 4,
            }),
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.source = 'form'
        service = self.cleaned_data.get('service', '')
        if service and instance.message:
            label = dict(SERVICE_CHOICES).get(service, service)
            instance.message = f'[{label}]\n{instance.message}'
        if commit:
            instance.save()
        return instance
