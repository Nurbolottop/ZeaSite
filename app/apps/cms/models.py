from django.db import models
from django_resized import ResizedImageField


COLOR_CHOICES = [
    ('indigo', 'Indigo'),
    ('purple', 'Purple'),
    ('cyan',   'Cyan'),
    ('blue',   'Blue'),
    ('green',  'Green'),
    ('pink',   'Pink'),
    ('orange', 'Orange'),
    ('red',    'Red'),
    ('yellow', 'Yellow'),
]


class Service(models.Model):
    title       = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    icon        = models.CharField('Иконка (lucide)', max_length=60, default='code-2',
                                   help_text='Используется если фото не загружено')
    image       = ResizedImageField(
                      '📷 Изображение услуги',
                      size=[800, 600], quality=88,
                      upload_to='services/', force_format='WEBP',
                      blank=True, null=True,
                      help_text='Иллюстрация / скриншот услуги (800×600, WebP)')
    color       = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order       = models.PositiveIntegerField('Порядок', default=0)
    is_active   = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering            = ['order']

    def __str__(self):
        return self.title


class Project(models.Model):
    name         = models.CharField('Название', max_length=100)
    description  = models.TextField('Описание')
    project_type = models.CharField('Тип проекта', max_length=100)
    technologies = models.CharField('Технологии', max_length=500,
                                    help_text='Через запятую: Django, React, Docker')
    icon         = models.CharField('Иконка (lucide)', max_length=60, default='layers',
                                    help_text='Используется если фото не загружено')
    image        = ResizedImageField(
                       '📷 Скриншот проекта',
                       size=[1200, 800], quality=88,
                       upload_to='projects/', force_format='WEBP',
                       blank=True, null=True,
                       help_text='Скриншот / превью проекта (1200×800, WebP)')
    color        = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    live_url     = models.URLField('🔗 Ссылка на проект', blank=True,
                                   help_text='URL живого сайта (кнопка "Открыть проект")')
    year         = models.PositiveIntegerField('Год', default=2024)
    order        = models.PositiveIntegerField('Порядок', default=0)
    is_active    = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering            = ['order']

    def __str__(self):
        return self.name

    @property
    def technologies_list(self):
        return [t.strip() for t in self.technologies.split(',') if t.strip()]


class Partner(models.Model):
    name     = models.CharField('Название', max_length=100)
    industry = models.CharField('Сфера', max_length=100)
    icon     = models.CharField('Иконка (lucide)', max_length=60, default='building-2',
                                help_text='Используется если логотип не загружен')
    logo     = ResizedImageField(
                   '🖼 Логотип',
                   size=[400, 400], quality=90,
                   upload_to='partners/', force_format='WEBP',
                   blank=True, null=True,
                   help_text='Логотип компании (400×400, WebP)')
    color    = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order    = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Партнёр'
        verbose_name_plural = 'Партнёры'
        ordering            = ['order']

    def __str__(self):
        return self.name


class TechStack(models.Model):
    name      = models.CharField('Название', max_length=50)
    label     = models.CharField('Метка (2-3 символа)', max_length=6)
    logo      = ResizedImageField(
                    '🖼 Логотип технологии',
                    size=[80, 80], quality=90,
                    upload_to='tech/', force_format='WEBP',
                    blank=True, null=True,
                    help_text='Квадратный логотип (80×80, WebP)')
    color     = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order     = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Технология'
        verbose_name_plural = 'Технологии'
        ordering            = ['order']

    def __str__(self):
        return self.name


class WhyUs(models.Model):
    title       = models.CharField('Заголовок', max_length=100)
    description = models.TextField('Описание')
    icon        = models.CharField('Иконка (lucide)', max_length=60, default='check-circle')
    image       = ResizedImageField(
                      '📷 Изображение',
                      size=[600, 400], quality=85,
                      upload_to='why/', force_format='WEBP',
                      blank=True, null=True,
                      help_text='Опционально — иллюстрация к пункту')
    color       = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order       = models.PositiveIntegerField('Порядок', default=0)
    is_active   = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Причина выбора'
        verbose_name_plural = 'Почему выбирают нас'
        ordering            = ['order']

    def __str__(self):
        return self.title


class Stat(models.Model):
    value_text     = models.CharField('Значение (текст)', max_length=100,
                                      help_text='Например: 5 (для счётчика) или CRM (текст)')
    label          = models.CharField('Подпись', max_length=100)
    suffix         = models.CharField('Суффикс', max_length=5, blank=True,
                                      help_text='Например: + (отображается после числа)')
    is_counter     = models.BooleanField('Анимированный счётчик', default=False)
    counter_target = models.PositiveIntegerField('Целевое число', null=True, blank=True,
                                                  help_text='Только для счётчиков')
    icon           = models.CharField('Иконка (lucide)', max_length=60, blank=True)
    description    = models.TextField('Описание (для широкой карточки)', blank=True)
    color          = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order          = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name        = 'Статистика'
        verbose_name_plural = 'Статистика'
        ordering            = ['order']

    def __str__(self):
        return f'{self.value_text} — {self.label}'


class SiteSettings(models.Model):
    # ── Брендинг ─────────────────────────────────────────────
    site_name    = models.CharField('Название сайта', max_length=100, default='ZEA')
    site_tagline = models.CharField('Слоган / подзаголовок бренда', max_length=200,
                                    default='IT Studio', blank=True)
    logo         = ResizedImageField(
                       '🖼 Логотип',
                       size=[600, 200], quality=92,
                       upload_to='brand/', force_format='WEBP',
                       blank=True, null=True,
                       help_text='Основной логотип сайта (PNG/SVG → WebP, 600×200)')
    logo_white   = ResizedImageField(
                       '🖼 Логотип (белый / для тёмного фона)',
                       size=[600, 200], quality=92,
                       upload_to='brand/', force_format='WEBP',
                       blank=True, null=True,
                       help_text='Белая версия логотипа (необязательно)')
    favicon      = ResizedImageField(
                       '🔲 Favicon',
                       size=[64, 64], quality=95,
                       upload_to='brand/', force_format='WEBP',
                       blank=True, null=True,
                       help_text='Иконка вкладки браузера (квадрат 64×64)')

    # ── SEO ──────────────────────────────────────────────────
    meta_title       = models.CharField('Meta title', max_length=120, blank=True,
                                        help_text='Заголовок страницы в поисковике (до 120 симв.)')
    meta_description = models.TextField('Meta description', blank=True, max_length=320,
                                        help_text='Описание для поисковиков и соцсетей (до 320 симв.)')
    meta_keywords    = models.CharField('Meta keywords', max_length=300, blank=True,
                                        help_text='Ключевые слова через запятую')
    og_image         = ResizedImageField(
                           '🌐 OG Image (превью в соцсетях)',
                           size=[1200, 630], quality=88,
                           upload_to='brand/', force_format='WEBP',
                           blank=True, null=True,
                           help_text='Картинка при шаринге ссылки (1200×630, WebP)')

    # ── Hero ─────────────────────────────────────────────────
    hero_badge    = models.CharField('Hero бейдж', max_length=100,
                                     default='Открыты для новых проектов')
    hero_title    = models.CharField('Hero заголовок', max_length=200,
                                     default='ZEA — разработка цифровых решений для бизнеса')
    hero_subtitle = models.TextField('Hero подзаголовок',
                                     default='Создаём сайты, CRM-системы, Telegram-ботов и внутренние '
                                             'платформы для автоматизации бизнес-процессов.')

    # ── О компании ───────────────────────────────────────────
    about_text = models.TextField('О компании',
                                  default='ZEA — мини IT-студия, которая помогает бизнесам запускать '
                                          'современные цифровые продукты. Мы разрабатываем сайты, '
                                          'CRM-системы, Telegram-ботов и решения для автоматизации '
                                          'процессов.')

    # ── Контакты ─────────────────────────────────────────────
    telegram_url   = models.URLField('Telegram URL',   blank=True, default='https://t.me/zea_studio')
    whatsapp_url   = models.URLField('WhatsApp URL',   blank=True, default='https://wa.me/996700000000')
    instagram_url  = models.URLField('Instagram URL',  blank=True,
                                     default='https://instagram.com/zea.studio')
    email          = models.EmailField('Email', blank=True, default='hello@zea.dev')

    # ── Подвал ───────────────────────────────────────────────
    footer_text    = models.CharField('Текст подвала', max_length=200, blank=True,
                                      default='© 2024 ZEA IT Studio. All rights reserved.')

    # ── Аналитика и индексация ───────────────────────────────
    site_domain      = models.URLField('Домен сайта', blank=True,
                           help_text='https://zea.kg — для canonical, sitemap, Open Graph')
    ga4_id           = models.CharField('Google Analytics 4 ID', max_length=20, blank=True,
                           help_text='G-XXXXXXXXXX')
    gsc_verification = models.CharField('Google Search Console — код', max_length=100, blank=True,
                           help_text='Значение content из meta google-site-verification')

    class Meta:
        verbose_name        = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return f'Настройки — {self.site_name}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def get_base_url(self, request=None):
        """Базовый URL сайта: домен из настроек, иначе из запроса."""
        if self.site_domain:
            return self.site_domain.rstrip('/')
        if request is not None:
            return f'{request.scheme}://{request.get_host()}'
        return ''

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
