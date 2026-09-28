from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Дата создания и последнего изменения записи."""

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)

    class Meta:
        abstract = True


class AuthoredModel(TimeStampedModel):
    """TimeStampedModel + кто создал / последним изменил запись.

    Поля заполняются в services.py (модель не знает о request).
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Создал',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Изменил',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False,
    )

    class Meta:
        abstract = True
