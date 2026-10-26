from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User


class AdminAuthenticationForm(AuthenticationForm):
    """Вход в админку по имени пользователя."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError('Неверное имя пользователя или пароль')

            self.user_cache = authenticate(
                self.request,
                username=user.email,
                password=password,
            )

            if self.user_cache is None:
                raise ValidationError('Неверное имя пользователя или пароль')

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
