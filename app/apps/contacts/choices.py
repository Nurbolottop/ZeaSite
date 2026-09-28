"""Единственный источник вариантов для формы заявки: из него строятся и поля
формы, и HTML (шаблон перебирает choices поля), и CooperationFormat.request_type."""
from django.utils.translation import gettext_lazy as _

REQUEST_TYPE_CHOICES = [
    ('partnership', _('Хочу обсудить партнёрство')),
    ('development', _('Нужна разработка')),
    ('other',       _('Другой вопрос')),
]

SERVICE_CHOICES = [
    ('website',     _('Сайт')),
    ('web_system',  _('Веб-система или платформа')),
    ('crm',         _('CRM и внутренние системы')),
    ('mobile',      _('Мобильное приложение')),
    ('automation',  _('Автоматизация')),
    ('integration', _('Интеграции')),
    ('support',     _('Сопровождение')),
    ('other',       _('Пока не знаю / другое')),
]
