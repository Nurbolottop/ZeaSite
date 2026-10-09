from django import forms
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from .models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings,
    CooperationFormat, ProcessStep, Commitment, TeamMember, ProjectImage,
)


# ── Готовый набор иконок (lucide), сгруппированный по категориям ─────────────
ICON_CHOICES = [
    ('Разработка', [
        ('code-2', 'code-2 — код'),
        ('terminal', 'terminal — терминал'),
        ('cpu', 'cpu — процессор'),
        ('server', 'server — сервер'),
        ('database', 'database — база данных'),
        ('cloud', 'cloud — облако'),
        ('box', 'box — коробка'),
        ('package', 'package — пакет'),
        ('layers', 'layers — слои'),
        ('git-branch', 'git-branch — ветка'),
        ('wrench', 'wrench — гаечный ключ'),
        ('plug', 'plug — интеграция'),
        ('workflow', 'workflow — процесс'),
        ('search-check', 'search-check — анализ'),
        ('life-buoy', 'life-buoy — сопровождение'),
    ]),
    ('Дизайн', [
        ('palette', 'palette — палитра'),
        ('pen-tool', 'pen-tool — перо'),
        ('image', 'image — картинка'),
        ('camera', 'camera — камера'),
        ('layout', 'layout — макет'),
        ('layout-grid', 'layout-grid — сетка'),
        ('monitor', 'monitor — монитор'),
        ('smartphone', 'smartphone — телефон'),
        ('pencil-ruler', 'pencil-ruler — проектирование'),
        ('app-window', 'app-window — веб-приложение'),
    ]),
    ('Бизнес', [
        ('briefcase', 'briefcase — портфель'),
        ('building-2', 'building-2 — здание'),
        ('store', 'store — магазин'),
        ('shopping-cart', 'shopping-cart — корзина'),
        ('credit-card', 'credit-card — карта'),
        ('dollar-sign', 'dollar-sign — доллар'),
        ('trending-up', 'trending-up — рост'),
        ('bar-chart-3', 'bar-chart-3 — график'),
        ('target', 'target — цель'),
        ('rocket', 'rocket — ракета'),
        ('award', 'award — награда'),
        ('handshake', 'handshake — рукопожатие'),
        ('graduation-cap', 'graduation-cap — обучение'),
        ('shirt', 'shirt — одежда'),
        ('building', 'building — строительство'),
        ('truck', 'truck — логистика'),
        ('stethoscope', 'stethoscope — медицина'),
        ('heart-pulse', 'heart-pulse — здоровье'),
        ('palmtree', 'palmtree — отдых'),
        ('bed', 'bed — гостиница'),
        ('party-popper', 'party-popper — мероприятия'),
        ('newspaper', 'newspaper — медиа'),
        ('file-text', 'file-text — документы'),
    ]),
    ('Связь', [
        ('message-circle', 'message-circle — чат'),
        ('message-square', 'message-square — сообщение'),
        ('mail', 'mail — почта'),
        ('send', 'send — отправить'),
        ('phone', 'phone — телефон'),
        ('bell', 'bell — уведомление'),
        ('headphones', 'headphones — поддержка'),
        ('users', 'users — команда'),
        ('user', 'user — пользователь'),
        ('bot', 'bot — бот'),
    ]),
    ('Действия и статусы', [
        ('zap', 'zap — молния'),
        ('sparkles', 'sparkles — искры'),
        ('star', 'star — звезда'),
        ('heart', 'heart — сердце'),
        ('shield', 'shield — щит'),
        ('shield-check', 'shield-check — защита'),
        ('lock', 'lock — замок'),
        ('settings', 'settings — настройки'),
        ('check-circle', 'check-circle — галочка'),
        ('check', 'check — выполнено'),
        ('refresh-cw', 'refresh-cw — обновление'),
        ('search', 'search — поиск'),
        ('globe', 'globe — глобус'),
        ('calendar', 'calendar — календарь'),
        ('clock', 'clock — часы'),
        ('map-pin', 'map-pin — метка'),
        ('info', 'info — инфо'),
    ]),
]


# ── Базовый класс с превью цвета/иконки ─────────────────────────────────────
class PreviewAdmin(TranslationAdmin):
    class Media:
        js = (
            'https://unpkg.com/lucide@latest/dist/umd/lucide.js',
            'admin/cms_preview.js',
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'icon':
            kwargs['widget'] = forms.Select(choices=[('', '— выберите иконку —')] + ICON_CHOICES)
            field = super().formfield_for_dbfield(db_field, request, **kwargs)
            field.required = False
            return field
        return super().formfield_for_dbfield(db_field, request, **kwargs)


# ── Общие действия ──────────────────────────────────────────────────────────
@admin.action(description='✓ Активировать выбранные')
def make_active(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f'Активировано: {updated}')


@admin.action(description='✗ Деактивировать выбранные')
def make_inactive(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f'Деактивировано: {updated}')


# ── Service ─────────────────────────────────────────────────────────────────
@admin.register(Service)
class ServiceAdmin(PreviewAdmin):
    list_display       = ('title', 'icon', 'color', 'order', 'is_active')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'color')
    search_fields      = ('title', 'description')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description'),
        }),
        ('Внешний вид', {
            'fields': ('illustration', 'icon', 'image', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── Project ─────────────────────────────────────────────────────────────────
class ProjectImageInline(TranslationTabularInline):
    model  = ProjectImage
    extra  = 1
    fields = ('image', 'kind', 'caption', 'order')


@admin.register(Project)
class ProjectAdmin(PreviewAdmin):
    inlines = [ProjectImageInline]
    list_display       = ('name', 'project_type', 'year', 'is_featured', 'order', 'is_active')
    list_display_links = ('name',)
    list_editable      = ('is_featured', 'order', 'is_active')
    list_filter        = ('is_active', 'is_featured', 'year', 'color')
    search_fields      = ('name', 'description', 'technologies')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'project_type', 'technologies'),
        }),
        ('Внешний вид', {
            'fields': ('logo', 'icon', 'image', 'color'),
        }),
        ('Ссылки и детали', {
            'fields': ('partner', 'live_url', 'year'),
        }),
        ('Кейс (окно «Подробнее»)', {
            'description': 'Заполняйте только проверенными фактами. Пустые поля не показываются.',
            'fields': ('task', 'solution', 'result', 'is_featured'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── Partner ─────────────────────────────────────────────────────────────────
@admin.register(Partner)
class PartnerAdmin(PreviewAdmin):
    list_display       = ('name', 'industry', 'color', 'order', 'is_active')
    list_display_links = ('name',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'color')
    search_fields      = ('name', 'industry')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'industry', 'about', 'website'),
        }),
        ('Внешний вид', {
            'fields': ('icon', 'logo', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── TechStack ───────────────────────────────────────────────────────────────
@admin.register(TechStack)
class TechStackAdmin(PreviewAdmin):
    list_display       = ('name', 'label', 'color', 'order', 'is_active')
    list_display_links = ('name',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'color')
    search_fields      = ('name', 'label')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'label'),
        }),
        ('Внешний вид', {
            'fields': ('logo', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── WhyUs ───────────────────────────────────────────────────────────────────
@admin.register(WhyUs)
class WhyUsAdmin(PreviewAdmin):
    list_display       = ('title', 'icon', 'color', 'order', 'is_active')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'color')
    search_fields      = ('title', 'description')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description'),
        }),
        ('Внешний вид', {
            'fields': ('icon', 'image', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── Stat ────────────────────────────────────────────────────────────────────
@admin.register(Stat)
class StatAdmin(PreviewAdmin):
    list_display       = ('value_text', 'suffix', 'label', 'is_counter', 'counter_target', 'order', 'is_active')
    list_display_links = ('value_text',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'is_counter')
    actions            = [make_active, make_inactive]
    search_fields      = ('value_text', 'label')
    ordering           = ('order',)

    fieldsets = (
        ('Основная информация', {
            'fields': ('value_text', 'suffix', 'label', 'description'),
        }),
        ('Счётчик', {
            'fields': ('is_counter', 'counter_target'),
        }),
        ('Внешний вид', {
            'fields': ('icon', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── CooperationFormat ───────────────────────────────────────────────────────
@admin.register(CooperationFormat)
class CooperationFormatAdmin(PreviewAdmin):
    list_display       = ('title', 'request_type', 'is_primary', 'order', 'is_active')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'is_primary')
    ordering           = ('order',)
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'audience', 'description', 'terms'),
        }),
        ('Кнопка', {
            'fields': ('cta_label', 'request_type'),
        }),
        ('Внешний вид', {
            'fields': ('illustration', 'icon', 'is_primary'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── ProcessStep ─────────────────────────────────────────────────────────────
@admin.register(ProcessStep)
class ProcessStepAdmin(TranslationAdmin):
    list_display       = ('order', 'title', 'is_active')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active',)
    ordering           = ('order',)
    actions            = [make_active, make_inactive]
    fields             = ('title', 'description', 'order', 'is_active')


# ── Commitment ──────────────────────────────────────────────────────────────
@admin.register(Commitment)
class CommitmentAdmin(PreviewAdmin):
    list_display       = ('title', 'icon', 'color', 'order', 'is_active')
    list_display_links = ('title',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'color')
    ordering           = ('order',)
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description'),
        }),
        ('Внешний вид', {
            'fields': ('icon', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── SiteSettings ────────────────────────────────────────────────────────────
@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationAdmin):

    fieldsets = (
        ('Брендинг', {
            'fields': ('site_name', 'site_tagline', 'logo', 'logo_white', 'favicon'),
        }),
        ('Hero-секция', {
            'fields': ('hero_badge', 'hero_title', 'hero_subtitle'),
        }),
        ('О компании', {
            'fields': ('about_text', 'about_photo', 'about_photo_caption'),
        }),
        ('Контактная информация', {
            'description': 'Незаполненный контакт на сайте не показывается.',
            'fields': ('telegram_url', 'whatsapp_url', 'instagram_url', 'email'),
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'og_image'),
        }),
        ('Подвал', {
            'classes': ('collapse',),
            'fields': ('footer_text',),
        }),
        ('Аналитика и индексация', {
            'classes': ('collapse',),
            'fields': ('site_domain', 'ga4_id', 'gsc_verification'),
        }),
    )

    def has_add_permission(self, request):
        # Синглтон — запрещаем создавать второй экземпляр
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ── TeamMember ──────────────────────────────────────────────────────────────
@admin.register(TeamMember)
class TeamMemberAdmin(TranslationAdmin):
    list_display       = ('name', 'role', 'order', 'is_active')
    list_display_links = ('name',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active',)
    search_fields      = ('name', 'role')
    ordering           = ('order',)
    actions            = [make_active, make_inactive]
    fields             = ('name', 'role', 'photo', 'order', 'is_active')
