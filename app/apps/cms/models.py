from django.db import models
from django_resized import ResizedImageField

from apps.contacts.choices import REQUEST_TYPE_CHOICES


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

# Иллюстрации направлений: templates/site/illustrations/<key>.html
ILLUSTRATION_CHOICES = [
    ('websites',     'Сайты'),
    ('platforms',    'Веб-системы и платформы'),
    ('crm',          'CRM и внутренние системы'),
    ('mobile',       'Мобильные приложения'),
    ('automation',   'Автоматизация'),
    ('integrations', 'Интеграции'),
    ('support',      'Сопровождение'),
    ('ai',           'AI и ассистенты'),
    ('partnership',  'Технологическое партнёрство'),
]

# Если иллюстрация не выбрана — подбирается по иконке
ICON_ILLUSTRATIONS = {
    'globe': 'websites', 'monitor': 'websites', 'layout': 'websites',
    'app-window': 'platforms', 'layout-grid': 'platforms', 'layers': 'platforms',
    'database': 'crm', 'users': 'crm',
    'smartphone': 'mobile',
    'workflow': 'automation', 'zap': 'automation', 'settings': 'automation',
    'plug': 'integrations', 'refresh-cw': 'integrations',
    'life-buoy': 'support', 'headphones': 'support', 'shield-check': 'support',
    'bot': 'ai', 'sparkles': 'ai', 'cpu': 'ai',
    'handshake': 'partnership',
}


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
                      help_text='Фото вместо иллюстрации (800×600, WebP). Пусто — показывается иллюстрация')
    illustration = models.CharField('Иллюстрация', max_length=20, choices=ILLUSTRATION_CHOICES,
                                    blank=True,
                                    help_text='Пусто — подбирается автоматически по иконке')
    color       = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order       = models.PositiveIntegerField('Порядок', default=0)
    is_active   = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering            = ['order']

    def __str__(self):
        return self.title

    @property
    def illustration_key(self):
        return self.illustration or ICON_ILLUSTRATIONS.get(self.icon, 'platforms')


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
    # ── Кейс (окно «Подробнее») ──
    task         = models.TextField('Задача', blank=True,
                                    help_text='Какую задачу бизнеса решали')
    solution     = models.TextField('Решение', blank=True,
                                    help_text='Что сделали')
    result       = models.TextField('Результат', blank=True,
                                    help_text='Только подтверждённый результат')
    is_featured  = models.BooleanField('Избранный кейс', default=False,
                                       help_text='Показывается первым и в карточках первого экрана')
    order        = models.PositiveIntegerField('Порядок', default=0)
    is_active    = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Проект сайта (кейс)'
        verbose_name_plural = 'Проекты сайта (кейсы)'
        ordering            = ['order']

    def __str__(self):
        return self.name

    @property
    def technologies_list(self):
        return [t.strip() for t in self.technologies.split(',') if t.strip()]


class ProjectImage(models.Model):
    """Скриншоты платформы в окне «Подробнее» проекта."""
    KIND_CHOICES = [('desktop', 'Компьютер'), ('mobile', 'Телефон')]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='gallery',
                                verbose_name='Проект')
    image   = ResizedImageField('📷 Скриншот', size=[1800, 2400], quality=85,
                                upload_to='projects/gallery/', force_format='WEBP',
                                help_text='Реальный скриншот платформы (без вымышленных данных)')
    kind    = models.CharField('Экран', max_length=10, choices=KIND_CHOICES, default='desktop',
                               help_text='Определяет рамку: окно браузера или телефон')
    caption = models.CharField('Подпись', max_length=150, blank=True)
    order   = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name        = 'Скриншот проекта'
        verbose_name_plural = 'Скриншоты проекта'
        ordering            = ['order', 'pk']

    def __str__(self):
        return f'{self.project} — {self.caption or self.get_kind_display()}'


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
        verbose_name        = 'Партнёр сайта (логотип)'
        verbose_name_plural = 'Партнёры сайта (логотипы)'
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
    is_active      = models.BooleanField('Активно', default=True)

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
                                    default='Технологический партнёр для бизнеса', blank=True)
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
                                     default='Технологический партнёр для бизнеса')
    hero_title    = models.CharField('Hero заголовок (H1)', max_length=200,
                                     default='ZEA — технологический партнёр для бизнеса')
    hero_subtitle = models.TextField('Hero подзаголовок',
                                     default='Проектируем, разрабатываем, запускаем и сопровождаем '
                                             'цифровые продукты. Работаем как ваша IT-команда: '
                                             'долгосрочно или под конкретную задачу.')

    # ── О компании ───────────────────────────────────────────
    about_text = models.TextField('О компании',
                                  default='ZEA создаёт цифровые продукты и системы для бизнеса — от '
                                          'сайтов и внутренних платформ до CRM, мобильных приложений '
                                          'и автоматизации. Мы не заканчиваем работу после запуска: '
                                          'сопровождаем продукт, развиваем его и адаптируем под новые '
                                          'задачи компании.')
    about_photo = ResizedImageField(
                      '📷 Фото для блока «О нас»',
                      size=[1400, 1050], quality=86,
                      upload_to='about/', force_format='WEBP',
                      blank=True, null=True,
                      help_text='Команда или офис (горизонтальное, ~4:3). Пусто — показывается иллюстрация')
    about_photo_caption = models.CharField('Подпись к фото', max_length=150, blank=True)

    # ── Контакты ─────────────────────────────────────────────
    # Пустое поле = контакт не показывается на сайте.
    telegram_url   = models.URLField('Telegram URL',   blank=True,
                                     help_text='Пусто — кнопка не показывается')
    whatsapp_url   = models.URLField('WhatsApp URL',   blank=True,
                                     help_text='Формат: https://wa.me/996XXXXXXXXX. Пусто — не показывается')
    instagram_url  = models.URLField('Instagram URL',  blank=True,
                                     help_text='Пусто — кнопка не показывается')
    email          = models.EmailField('Email', blank=True,
                                       help_text='Пусто — кнопка не показывается')

    # ── Подвал ───────────────────────────────────────────────
    footer_text    = models.CharField('Текст подвала', max_length=200, blank=True,
                                      help_text='Пусто — «© <текущий год> ZEA»')

    # ── Аналитика и индексация ───────────────────────────────
    site_domain      = models.URLField('Домен сайта', blank=True,
                           help_text='https://zeastudio.su — для canonical, sitemap, Open Graph')
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


# ── Блоки нового позиционирования ───────────────────────────────────────────

FORMAT_ILLUSTRATION_CHOICES = [
    ('partnership',   'Сцепленные кольца — одна команда надолго'),
    ('revenue_share', 'Рост дохода и доля ZEA — партнёрство за процент'),
    ('development',   'Этапы до сдачи — проект под заказ'),
]


class CooperationFormat(models.Model):
    """Форматы сотрудничества (технологическое партнёрство / разработка под заказ)."""
    title        = models.CharField('Название', max_length=120)
    audience     = models.CharField('Для кого', max_length=250, blank=True)
    description  = models.TextField('Описание')
    terms        = models.CharField('Условия (строка внизу)', max_length=250, blank=True,
                                    help_text='Без процентов и сумм — условия обсуждаются индивидуально')
    cta_label    = models.CharField('Текст кнопки', max_length=60)
    request_type = models.CharField('Тип обращения в форме', max_length=20,
                                    choices=REQUEST_TYPE_CHOICES, default='partnership',
                                    help_text='Кнопка открывает форму с этим типом обращения')
    icon         = models.CharField('Иконка (lucide)', max_length=60, default='handshake')
    illustration = models.CharField('Иллюстрация', max_length=20, choices=FORMAT_ILLUSTRATION_CHOICES,
                                    blank=True,
                                    help_text='Пусто — автоматически: основной формат — кольца, иконка «рост» '
                                              'или «доллар» — доля в доходе, разработка — этапы до сдачи')
    is_primary   = models.BooleanField('Основной формат', default=False,
                                       help_text='Выделяется визуально')
    order        = models.PositiveIntegerField('Порядок', default=0)
    is_active    = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Формат сотрудничества'
        verbose_name_plural = 'Форматы сотрудничества'
        ordering            = ['order']

    def __str__(self):
        return self.title

    @property
    def illustration_key(self):
        if self.illustration:
            return self.illustration
        if self.is_primary:
            return 'partnership'
        if self.icon in ('trending-up', 'dollar-sign', 'bar-chart-3'):
            return 'revenue_share'
        return 'development' if self.request_type == 'development' else 'partnership'


class ProcessStep(models.Model):
    """Шаги блока «Как мы начинаем работу». Номер шага = позиция в списке."""
    title       = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    order       = models.PositiveIntegerField('Порядок', default=0)
    is_active   = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Шаг работы'
        verbose_name_plural = 'Как мы начинаем работу'
        ordering            = ['order']

    def __str__(self):
        return self.title


class Commitment(models.Model):
    """Пункты блока «Что мы берём на себя»."""
    title       = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    icon        = models.CharField('Иконка (lucide)', max_length=60, default='check-circle')
    color       = models.CharField('Цвет', max_length=20, choices=COLOR_CHOICES, default='indigo')
    order       = models.PositiveIntegerField('Порядок', default=0)
    is_active   = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Что берём на себя'
        verbose_name_plural = 'Что мы берём на себя'
        ordering            = ['order']

    def __str__(self):
        return self.title


class TeamMember(models.Model):
    """Команда на публичном сайте (блок «О нас»). Не связано с сотрудниками ZEA Hub."""
    name      = models.CharField('Имя', max_length=100)
    role      = models.CharField('Роль', max_length=120, blank=True)
    photo     = ResizedImageField(
                    '📷 Фото',
                    size=[600, 750], crop=['middle', 'center'], quality=86,
                    upload_to='team/', force_format='WEBP',
                    blank=True, null=True,
                    help_text='Вертикальное фото 4:5 (600×750). Пусто — инициалы')
    order     = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name        = 'Человек в команде'
        verbose_name_plural = 'Команда (на сайте)'
        ordering            = ['order']

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return ''.join(part[0] for part in self.name.split()[:2]).upper()
