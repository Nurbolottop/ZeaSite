"""Проекты партнёров ZEA.

Статус меняется только через services.change_project_status() (история,
причина паузы/отмены, возобновление в прежний статус). PM и технический
руководитель назначаются только сервисом — с проверкой роли пользователя.
"""
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.contracts.models import Contract
from apps.hub.models import AuthoredModel
from apps.partners.models import Company
from apps.team.models import Specialization


class ProjectType(models.TextChoices):
    WEBSITE = 'website', 'Сайт'
    WEB_SYSTEM = 'web_system', 'Веб-система'
    MOBILE_APP = 'mobile_app', 'Мобильное приложение'
    CRM = 'crm', 'CRM / внутренняя система'
    AUTOMATION = 'automation', 'Автоматизация'
    INTEGRATION = 'integration', 'Интеграция'
    OTHER = 'other', 'Другое'


class ProjectStatus(models.TextChoices):
    PLANNING = 'planning', 'Планирование'
    DEVELOPMENT = 'development', 'Разработка'
    TESTING = 'testing', 'Тестирование'
    MVP = 'mvp', 'MVP'
    LAUNCHED = 'launched', 'Запущен'
    SUPPORT = 'support', 'Сопровождение'
    PAUSED = 'paused', 'Приостановлен'
    CANCELLED = 'cancelled', 'Отменён'


# Рабочие статусы — из них можно поставить на паузу и в них возобновить
WORKING_STATUSES = (
    ProjectStatus.PLANNING, ProjectStatus.DEVELOPMENT, ProjectStatus.TESTING,
    ProjectStatus.MVP, ProjectStatus.LAUNCHED, ProjectStatus.SUPPORT,
)


class Priority(models.TextChoices):
    LOW = 'low', 'Низкий'
    MEDIUM = 'medium', 'Средний'
    HIGH = 'high', 'Высокий'
    CRITICAL = 'critical', 'Критичный'


PRIORITY_ORDER = {p: i for i, p in enumerate((Priority.CRITICAL, Priority.HIGH,
                                              Priority.MEDIUM, Priority.LOW))}


class Project(AuthoredModel):
    company = models.ForeignKey(Company, verbose_name='Компания', on_delete=models.PROTECT,
                                related_name='projects')
    contract = models.ForeignKey(Contract, verbose_name='Договор', on_delete=models.PROTECT,
                                 related_name='projects')
    name = models.CharField('Название', max_length=255)
    code = models.CharField(
        'Код', max_length=30,
        validators=[RegexValidator(r'^[A-Z0-9][A-Z0-9-]*$',
                                   'Код: заглавные латинские буквы, цифры и дефис, например KE-CRM.')],
    )
    description = models.TextField('Описание', blank=True)
    project_type = models.CharField('Тип проекта', max_length=20, choices=ProjectType.choices)
    project_type_other = models.CharField('Тип — описание', max_length=150, blank=True,
                                          help_text='Обязательно для типа «Другое».')

    status = models.CharField('Статус', max_length=20, choices=ProjectStatus.choices,
                              default=ProjectStatus.PLANNING, editable=False, db_index=True)
    status_changed_at = models.DateTimeField('Статус изменён', default=timezone.now, editable=False)
    # Статус до паузы — в него проект возвращается при возобновлении
    paused_from_status = models.CharField('Статус до паузы', max_length=20,
                                          choices=ProjectStatus.choices, blank=True, editable=False)
    priority = models.CharField('Приоритет', max_length=20, choices=Priority.choices,
                                default=Priority.MEDIUM)

    start_date = models.DateField('Дата начала', null=True, blank=True)
    planned_end_date = models.DateField('Плановое завершение', null=True, blank=True)
    actual_end_date = models.DateField('Фактическое завершение', null=True, blank=True)
    launch_date = models.DateField('Дата запуска', null=True, blank=True, editable=False,
                                   help_text='Проставляется при первом переходе в «Запущен».')

    pm = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='PM', on_delete=models.PROTECT,
                           related_name='managed_projects')
    technical_lead = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Технический руководитель',
                                       on_delete=models.PROTECT, related_name='led_projects')
    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(fields=['code'], name='projects_unique_code')]

    def __str__(self):
        return f'{self.code} — {self.name}'

    def get_absolute_url(self):
        return reverse('projects:detail', args=[self.pk])

    @property
    def type_display(self):
        if self.project_type == ProjectType.OTHER and self.project_type_other:
            return self.project_type_other
        return self.get_project_type_display()

    @property
    def is_overdue(self):
        return (self.planned_end_date is not None and self.actual_end_date is None
                and self.status in (ProjectStatus.PLANNING, ProjectStatus.DEVELOPMENT,
                                    ProjectStatus.TESTING, ProjectStatus.MVP)
                and self.planned_end_date < timezone.localdate())

    def clean(self):
        errors = {}
        if self.project_type == ProjectType.OTHER and not self.project_type_other.strip():
            errors['project_type_other'] = 'Опишите тип проекта.'
        if self.contract_id and self.company_id and self.contract.company_id != self.company_id:
            errors['contract'] = 'Договор принадлежит другой компании.'
        if self.start_date and self.planned_end_date and self.planned_end_date < self.start_date:
            errors['planned_end_date'] = 'Плановое завершение раньше даты начала.'
        if self.start_date and self.actual_end_date and self.actual_end_date < self.start_date:
            errors['actual_end_date'] = 'Фактическое завершение раньше даты начала.'
        if errors:
            raise ValidationError(errors)


class ProjectStatusHistory(models.Model):
    project = models.ForeignKey(Project, verbose_name='Проект', on_delete=models.CASCADE,
                                related_name='status_history')
    from_status = models.CharField('Из статуса', max_length=20, choices=ProjectStatus.choices, blank=True)
    to_status = models.CharField('В статус', max_length=20, choices=ProjectStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Изменил',
                                   on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    changed_at = models.DateTimeField('Дата', default=timezone.now)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Изменение статуса проекта'
        verbose_name_plural = 'История статусов проектов'
        ordering = ('-changed_at', '-id')

    def __str__(self):
        return f'{self.project}: {self.get_from_status_display() or "—"} → {self.get_to_status_display()}'


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, verbose_name='Проект', on_delete=models.CASCADE,
                                related_name='members')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Сотрудник',
                               on_delete=models.PROTECT, related_name='project_memberships')
    specialization = models.ForeignKey(Specialization, verbose_name='Роль в проекте',
                                       on_delete=models.PROTECT, related_name='+')
    joined_at = models.DateField('В проекте с', default=timezone.localdate)
    left_at = models.DateField('Вышел из проекта', null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    note = models.CharField('Заметка', max_length=255, blank=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Добавил',
                                 on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        verbose_name = 'Участник проекта'
        verbose_name_plural = 'Участники проектов'
        ordering = ('-is_active', 'joined_at')
        constraints = [
            # один человек не может дважды активно состоять в проекте в одной роли
            models.UniqueConstraint(fields=['project', 'member', 'specialization'],
                                    condition=Q(is_active=True),
                                    name='projects_unique_active_member_role'),
        ]

    def __str__(self):
        return f'{self.member} — {self.specialization} ({self.project.code})'


# ── Техническая информация ────────────────────────────────────────────────

# Признаки секретов. Хранить пароли, ключи и токены в Hub запрещено.
SECRET_PATTERNS = [
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'), 'приватный ключ'),
    (re.compile(r'(?i)\b(password|passwd|pwd|пароль|secret|секрет|api[_-]?key|token|токен)\s*[:=]\s*\S+'),
     'пароль / секрет / токен'),
    (re.compile(r'\b(ghp|gho|ghs|github_pat|glpat|xox[abp])[_-][A-Za-z0-9_]{10,}'), 'токен Git / Slack'),
    (re.compile(r'\bsk-[A-Za-z0-9_-]{20,}'), 'API-ключ'),
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'ключ AWS'),
    (re.compile(r'\b\d{8,10}:[A-Za-z0-9_-]{35}\b'), 'токен Telegram-бота'),
    (re.compile(r'[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@'), 'логин и пароль в URL'),
]


def find_secrets(text):
    return sorted({label for pattern, label in SECRET_PATTERNS if pattern.search(text or '')})


class ProjectTechnicalInfo(AuthoredModel):
    """Техническая информация проекта — отдельно от основной карточки.

    НЕ для секретов: пароли, SSH-ключи, токены, пароли БД здесь хранить нельзя
    (проверяется в clean()). Секреты — в менеджере паролей / секретах сервера.
    """

    project = models.OneToOneField(Project, verbose_name='Проект', on_delete=models.CASCADE,
                                   related_name='technical_info')
    repository_url = models.URLField('Репозиторий', blank=True)
    production_url = models.URLField('Production', blank=True)
    staging_url = models.URLField('Staging', blank=True)
    technology_stack = models.TextField('Стек технологий', blank=True)
    server_info = models.TextField('Серверы и окружение', blank=True,
                                   help_text='Хостинг, регион, тип сервера — без IP-доступов и паролей.')
    deployment_notes = models.TextField('Деплой', blank=True)
    technical_notes = models.TextField('Технические заметки', blank=True)

    TEXT_FIELDS = ('repository_url', 'production_url', 'staging_url', 'technology_stack',
                   'server_info', 'deployment_notes', 'technical_notes')

    class Meta:
        verbose_name = 'Техническая информация проекта'
        verbose_name_plural = 'Техническая информация проектов'

    def __str__(self):
        return f'Техинфо: {self.project}'

    def clean(self):
        errors = {}
        for field in self.TEXT_FIELDS:
            found = find_secrets(getattr(self, field))
            if found:
                errors[field] = (f'Похоже на секрет ({", ".join(found)}). '
                                 'Пароли, ключи и токены в Hub хранить нельзя.')
        if errors:
            raise ValidationError(errors)
