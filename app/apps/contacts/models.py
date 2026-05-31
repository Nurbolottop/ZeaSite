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
