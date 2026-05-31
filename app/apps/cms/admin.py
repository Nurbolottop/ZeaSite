from django import forms
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings


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
            'fields': ('icon', 'image', 'color'),
        }),
        ('Отображение', {
            'classes': ('collapse',),
            'fields': ('order', 'is_active'),
        }),
    )


# ── Project ─────────────────────────────────────────────────────────────────
@admin.register(Project)
class ProjectAdmin(PreviewAdmin):
    list_display       = ('name', 'project_type', 'year', 'color', 'order', 'is_active')
    list_display_links = ('name',)
    list_editable      = ('order', 'is_active')
    list_filter        = ('is_active', 'year', 'color')
    search_fields      = ('name', 'description', 'technologies')
    ordering           = ('order',)
    list_per_page      = 25
    actions            = [make_active, make_inactive]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'project_type', 'technologies'),
        }),
        ('Внешний вид', {
            'fields': ('icon', 'image', 'color'),
        }),
        ('Ссылки и детали', {
            'fields': ('live_url', 'year'),
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
            'fields': ('name', 'industry'),
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
    list_display       = ('value_text', 'suffix', 'label', 'is_counter', 'counter_target', 'order')
    list_display_links = ('value_text',)
    list_editable      = ('order',)
    list_filter        = ('is_counter',)
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
            'fields': ('order',),
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
            'fields': ('about_text',),
        }),
        ('Контактная информация', {
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
