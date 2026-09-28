"""Команда ZEA.

Роль доступа (Django Group: «Технический руководитель», «DevOps»…) и
специализация сотрудника («Backend Developer»…) — разные вещи:
роли определяют права в Hub, специализации — чем человек занимается.
Персональные контакты (телефон, аватар) — в users.HubProfile, здесь не дублируются.
"""
from django.conf import settings
from django.db import models

from apps.hub.models import TimeStampedModel


class Specialization(models.Model):
    """Справочник специализаций. Расширяется в админке без миграций."""

    name = models.CharField('Название', max_length=100, unique=True)
    is_technical = models.BooleanField(
        'Техническая', default=True,
        help_text='Участников с технической специализацией может добавлять в проект '
                  'технический руководитель проекта.',
    )
    is_active = models.BooleanField('Используется', default=True)
    sort_order = models.PositiveSmallIntegerField('Порядок', default=100)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        ordering = ('sort_order', 'name')

    def __str__(self):
        return self.name


class EmploymentType(models.TextChoices):
    FULL_TIME = 'full_time', 'Полная занятость'
    PART_TIME = 'part_time', 'Частичная занятость'
    CONTRACTOR = 'contractor', 'Подрядчик / фриланс'


class EmployeeProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='Пользователь',
                                on_delete=models.CASCADE, related_name='employee')
    position = models.CharField('Должность', max_length=150, blank=True)
    employment_type = models.CharField('Тип работы', max_length=20, choices=EmploymentType.choices,
                                       default=EmploymentType.FULL_TIME)
    specializations = models.ManyToManyField(Specialization, verbose_name='Специализации',
                                             related_name='employees', blank=True)
    started_at = models.DateField('Дата начала работы', null=True, blank=True)
    is_active = models.BooleanField('Работает в команде', default=True)
    note = models.TextField('Заметка', blank=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ('user__first_name', 'user__last_name', 'user__username')

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()
