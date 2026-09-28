from django import forms


class BootstrapFormMixin:
    """Проставляет Bootstrap-классы виджетам формы."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.RadioSelect)):
                css = 'form-check-input'
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()
            if isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('rows', 3)

    def full_clean(self):
        super().full_clean()
        # Подсветка полей с ошибками
        for name in self.errors:
            if name in self.fields:
                widget = self.fields[name].widget
                widget.attrs['class'] = f"{widget.attrs.get('class', '')} is-invalid".strip()
