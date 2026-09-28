from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Логин', 'autofocus': True}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Пароль'}
        )
