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


class BriefForm(forms.Form):
    """Форма брифа: поля строятся из brief.STEPS."""

    website = forms.CharField(required=False)   # ловушка для спам-ботов, людям не видна

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .brief import STEPS
        for step in STEPS:
            for f in step['fields']:
                kind, req, label = f['kind'], f['required'], f['label']
                if kind == 'multi':
                    field = forms.MultipleChoiceField(choices=f['options'], required=req, label=label)
                elif kind == 'radio':
                    field = forms.ChoiceField(choices=f['options'], required=req, label=label)
                elif kind == 'consent':
                    field = forms.BooleanField(required=True, label=label)
                elif kind == 'email':
                    field = forms.EmailField(required=req, label=label, max_length=254)
                elif kind == 'textarea':
                    field = forms.CharField(required=req, label=label, max_length=4000)
                else:
                    field = forms.CharField(required=req, label=label, max_length=200)
                self.fields[f['key']] = field

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('website'):
            raise forms.ValidationError(_('Не удалось отправить бриф.'))
        if not any((cleaned.get(k) or '').strip() for k in ('phone', 'email', 'telegram')):
            raise forms.ValidationError(_('Укажите телефон, email или Telegram — чтобы мы могли связаться с вами.'))
        return cleaned

    def answers_ru(self):
        """Ответы по шагам с русскими подписями — для админки."""
        from .brief import STEPS
        data, result = self.cleaned_data, []
        with translation.override('ru'):
            for step in STEPS:
                items = []
                for f in step['fields']:
                    if f['kind'] == 'consent':
                        continue
                    value = data.get(f['key'])
                    if not value:
                        continue
                    options = dict(f['options'])
                    if f['kind'] == 'multi':
                        value = ', '.join(str(options.get(v, v)) for v in value)
                    elif f['kind'] == 'radio':
                        value = str(options.get(value, value))
                    items.append({'label': str(f['label']), 'value': str(value).strip()})
                if items:
                    result.append({'step': str(step['title']), 'items': items})
        return result

    def save(self):
        from .models import Brief
        data = self.cleaned_data
        from .brief import FIELDS
        with translation.override('ru'):
            def label(key, code):
                return str(dict(FIELDS[key]['options']).get(code, code)) if code else ''
            products = ', '.join(label('product_types', c) for c in data.get('product_types') or [])
            deadline, budget = label('deadline', data.get('deadline')), label('budget', data.get('budget'))
        return Brief.objects.create(
            name=data['name'].strip()[:100], company=(data.get('company') or '').strip()[:150],
            phone=(data.get('phone') or '').strip()[:30], email=(data.get('email') or '').strip(),
            telegram=(data.get('telegram') or '').strip()[:64], product_types=products[:300],
            deadline=deadline[:60], budget=budget[:60], answers=self.answers_ru(),
            language=translation.get_language() or 'ru',
        )
