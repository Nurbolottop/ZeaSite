"""Компании: кандидат и партнёр — одна и та же Company на разных статусах.

Статус меняется только через services.change_status() — он проверяет переход
и пишет CompanyStatusHistory. Напрямую company.status не присваивать.
"""
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.hub.models import AuthoredModel


class CompanyType(models.TextChoices):
    BUSINESS = 'business', 'Действующий бизнес'
    STARTUP = 'startup', 'Стартап'


class CompanyStatus(models.TextChoices):
    NEW = 'new', 'Новый'
    ANALYSIS = 'analysis', 'Анализ'
    DISCUSSION = 'discussion', 'Обсуждение'
    APPROVED = 'approved', 'Одобрен'
    NEGOTIATION = 'negotiation', 'Переговоры'
    CONTRACT = 'contract', 'Договор'
    PARTNER = 'partner', 'Партнёр'
    REJECTED = 'rejected', 'Отклонён'


class CompanySource(models.TextChoices):
    REFERRAL = 'referral', 'Рекомендация'
    INBOUND = 'inbound', 'Входящее обращение'
    OUTREACH = 'outreach', 'Собственный поиск'
    SOCIAL = 'social', 'Соцсети'
    EVENT = 'event', 'Мероприятие'
    OTHER = 'other', 'Другое'


class Company(AuthoredModel):
    name = models.CharField('Название', max_length=255)
    legal_name = models.CharField('Юридическое название', max_length=255, blank=True)
    company_type = models.CharField('Тип', max_length=20, choices=CompanyType.choices,
                                    default=CompanyType.BUSINESS)
    industry = models.CharField('Сфера бизнеса', max_length=255, blank=True)
    description = models.TextField('Краткое описание', blank=True)

    website = models.URLField('Сайт', blank=True)
    instagram = models.CharField('Instagram', max_length=255, blank=True)
    phone = models.CharField('Телефон', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    city = models.CharField('Город', max_length=100, blank=True)

    source = models.CharField('Источник', max_length=20, choices=CompanySource.choices, blank=True)
    source_details = models.CharField('Источник — подробнее', max_length=255, blank=True,
                                      help_text='Кто порекомендовал, какое мероприятие и т.п.')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Ответственный менеджер',
        on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_companies',
    )

    status = models.CharField('Статус', max_length=20, choices=CompanyStatus.choices,
                              default=CompanyStatus.NEW, editable=False, db_index=True)
    status_changed_at = models.DateTimeField('Статус изменён', default=timezone.now, editable=False)
    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    @property
    def is_partner(self):
        return self.status == CompanyStatus.PARTNER

    def get_absolute_url(self):
        # Одна карточка, но в разделе «Партнёры» или «Кандидаты» по статусу
        if self.is_partner:
            return reverse('partners:detail', args=[self.pk])
        return reverse('candidates:detail', args=[self.pk])


class CompanyStatusHistory(models.Model):
    company = models.ForeignKey(Company, verbose_name='Компания', on_delete=models.CASCADE,
                                related_name='status_history')
    from_status = models.CharField('Из статуса', max_length=20, choices=CompanyStatus.choices, blank=True)
    to_status = models.CharField('В статус', max_length=20, choices=CompanyStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Изменил',
                                   on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    changed_at = models.DateTimeField('Дата', default=timezone.now)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Изменение статуса'
        verbose_name_plural = 'История статусов'
        ordering = ('-changed_at', '-id')

    def __str__(self):
        return f'{self.company}: {self.get_from_status_display() or "—"} → {self.get_to_status_display()}'


class CompanyContact(models.Model):
    company = models.ForeignKey(Company, verbose_name='Компания', on_delete=models.CASCADE,
                                related_name='contacts')
    name = models.CharField('Имя', max_length=255)
    position = models.CharField('Должность', max_length=255, blank=True)
    phone = models.CharField('Телефон', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    telegram = models.CharField('Telegram', max_length=100, blank=True)
    is_primary = models.BooleanField('Основной контакт', default=False)
    note = models.TextField('Заметка', blank=True)

    class Meta:
        verbose_name = 'Контактное лицо'
        verbose_name_plural = 'Контактные лица'
        ordering = ('-is_primary', 'name')
        constraints = [
            models.UniqueConstraint(fields=['company'], condition=Q(is_primary=True),
                                    name='partners_one_primary_contact'),
        ]

    def __str__(self):
        return self.name


class FinancialTransparency(models.TextChoices):
    HIGH = 'high', 'Высокая — данные предоставлены'
    PARTIAL = 'partial', 'Частичная'
    LOW = 'low', 'Низкая — данные скрываются'


class MvpState(models.TextChoices):
    YES = 'yes', 'Есть'
    IN_PROGRESS = 'in_progress', 'В разработке'
    NO = 'no', 'Нет'


class CandidateAssessment(AuthoredModel):
    """Аналитическая карточка компании перед решением (одна на компанию).

    Итоговый балл намеренно не считается — это структурированные заметки.
    """

    company = models.OneToOneField(Company, verbose_name='Компания', on_delete=models.CASCADE,
                                   related_name='assessment')

    # Бизнес
    business_model = models.TextField('Бизнес-модель', blank=True)
    products = models.TextField('Текущий продукт / услуги', blank=True)
    target_audience = models.TextField('Целевая аудитория', blank=True)
    team_info = models.TextField('Команда', blank=True)
    market_analysis = models.TextField('Анализ рынка', blank=True)
    development_plan = models.TextField('План развития компании', blank=True)

    # IT
    it_state = models.TextField('Текущее состояние IT', blank=True)
    problem = models.TextField('Какую проблему нужно решить', blank=True)
    proposed_solution = models.TextField('Какое IT-решение можем предложить', blank=True)
    mvp_state = models.CharField('MVP', max_length=20, choices=MvpState.choices, blank=True)

    # Финансы. Текстом: валюта/период у компаний разные, раскрываются частично.
    revenue = models.CharField('Текущая выручка', max_length=255, blank=True,
                               help_text='Если компания раскрыла, например «≈ 800 000 сом/мес»')
    financial_indicator = models.CharField('Минимальный доход / фин. показатель', max_length=255,
                                           blank=True)
    financial_transparency = models.CharField('Прозрачность финансов', max_length=20,
                                              choices=FinancialTransparency.choices, blank=True)

    # Риски
    legal_risks = models.TextField('Налоговые / юридические риски', blank=True)
    reputation = models.TextField('Клиентская репутация', blank=True)
    risks_for_zea = models.TextField('Потенциальные риски для ZEA', blank=True)

    manager_comment = models.TextField('Комментарий менеджера по развитию', blank=True)

    class Meta:
        verbose_name = 'Анализ кандидата'
        verbose_name_plural = 'Анализ кандидатов'

    def __str__(self):
        return f'Анализ: {self.company}'


class DecisionResult(models.TextChoices):
    REWORK = 'rework', 'На доработку'
    APPROVE = 'approve', 'Одобрить'
    REJECT = 'reject', 'Отклонить'


class CandidateDecision(AuthoredModel):
    """Решение основного состава по кандидату. Запись не редактируется."""

    company = models.ForeignKey(Company, verbose_name='Компания', on_delete=models.CASCADE,
                                related_name='decisions')
    review_date = models.DateField('Дата рассмотрения', default=timezone.localdate)
    decision = models.CharField('Решение', max_length=20, choices=DecisionResult.choices)
    comment = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'Решение по кандидату'
        verbose_name_plural = 'Решения по кандидатам'
        ordering = ('-review_date', '-created_at')

    def __str__(self):
        return f'{self.company}: {self.get_decision_display()} ({self.review_date:%d.%m.%Y})'
