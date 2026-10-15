from django.db import models


class ContactMessage(models.Model):
    SOURCE_CHOICES = [
        ('telegram',   'Telegram'),
        ('whatsapp',   'WhatsApp'),
        ('instagram',  'Instagram'),
        ('email',      'Email'),
        ('form',       'Форма сайта'),
        ('other',      'Другое'),
    ]

    name       = models.CharField('Имя', max_length=100, blank=True)
    email      = models.EmailField('Email', blank=True)
    phone      = models.CharField('Телефон', max_length=30, blank=True)
    message    = models.TextField('Сообщение')
    source     = models.CharField('Источник', max_length=20,
                                  choices=SOURCE_CHOICES, default='form')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    is_read    = models.BooleanField('Прочитано', default=False)

    class Meta:
        verbose_name        = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.name or "Аноним"} — {self.created_at:%d.%m.%Y %H:%M}'


class Brief(models.Model):
    """Бриф проекта со страницы /brief/. Все ответы — в answers (по шагам,
    подписи на русском для чтения в админке), ключевые — отдельными полями."""
    STATUS_CHOICES = [
        ('new',         'Новый'),
        ('in_progress', 'В работе'),
        ('done',        'Обработан'),
    ]

    name          = models.CharField('Имя', max_length=100)
    company       = models.CharField('Компания', max_length=150, blank=True)
    phone         = models.CharField('Телефон', max_length=30, blank=True)
    email         = models.EmailField('Email', blank=True)
    telegram      = models.CharField('Telegram', max_length=64, blank=True)
    product_types = models.CharField('Что нужно', max_length=300, blank=True)
    deadline      = models.CharField('Сроки', max_length=60, blank=True)
    budget        = models.CharField('Бюджет', max_length=60, blank=True)
    answers       = models.JSONField('Ответы', default=list)
    language      = models.CharField('Язык', max_length=5, blank=True)
    status        = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    note          = models.TextField('Заметка менеджера', blank=True)
    created_at    = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        verbose_name        = 'Бриф'
        verbose_name_plural = 'Брифы'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.name}{" — " + self.company if self.company else ""} ({self.created_at:%d.%m.%Y})'
