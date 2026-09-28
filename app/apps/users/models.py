import os
import uuid

from django.conf import settings
from django.db import models


def avatar_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f'hub/avatars/{uuid.uuid4().hex}{ext}'


class HubProfile(models.Model):
    """Данные сотрудника ZEA Hub поверх стандартного django.contrib.auth User.

    Стандартный User сохранён сознательно: prod-БД сайта уже использует
    auth.User, а смена AUTH_USER_MODEL на существующей БД небезопасна.
    Роли — через Groups (см. apps.users.roles). Профиль необязателен:
    используйте apps.users.profile.get_hub_profile().
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name='Пользователь',
        on_delete=models.CASCADE, related_name='hub_profile',
    )
    phone = models.CharField('Телефон', max_length=30, blank=True)
    avatar = models.ImageField('Аватар', upload_to=avatar_upload_to, blank=True)

    class Meta:
        verbose_name = 'Профиль сотрудника'
        verbose_name_plural = 'Профили сотрудников'

    def __str__(self):
        return f'Профиль {self.user}'
