from django.contrib import admin
from django.utils.html import format_html, format_html_join, linebreaks
from .models import Brief, ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display       = ('created_at', 'name', 'phone', 'email', 'source', 'is_read')
    list_display_links = ('name',)
    list_editable      = ('is_read',)
    list_filter        = ('is_read', 'source', 'created_at')
    search_fields      = ('name', 'email', 'phone', 'message')
    ordering           = ('-created_at',)
    date_hierarchy     = 'created_at'
    list_per_page      = 30
    readonly_fields    = ('name', 'email', 'phone', 'message', 'source', 'created_at')
    actions            = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Заявка', {
            'fields': ('name', 'phone', 'email', 'message'),
        }),
        ('Служебное', {
            'fields': ('source', 'created_at', 'is_read'),
        }),
    )

    @admin.action(description='Отметить как прочитанные')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Отмечено прочитанными: {updated}')

    @admin.action(description='Отметить как непрочитанные')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'Отмечено непрочитанными: {updated}')

    def has_add_permission(self, request):
        # Заявки создаются только с сайта
        return False


@admin.register(Brief)
class BriefAdmin(admin.ModelAdmin):
    list_display       = ('created_at', 'name', 'company', 'product_types', 'deadline', 'budget', 'status')
    list_display_links = ('name',)
    list_editable      = ('status',)
    list_filter        = ('status', 'language', 'created_at')
    search_fields      = ('name', 'company', 'phone', 'email', 'telegram', 'product_types')
    date_hierarchy     = 'created_at'
    list_per_page      = 30
    readonly_fields    = ('brief_document', 'name', 'company', 'phone', 'email', 'telegram',
                          'language', 'created_at')
    fieldsets = (
        ('Бриф', {'fields': ('brief_document',)}),
        ('Контакты', {'fields': ('name', 'company', 'phone', 'email', 'telegram')}),
        ('Работа с брифом', {'fields': ('status', 'note', 'language', 'created_at')}),
    )

    @admin.display(description='Ответы клиента')
    def brief_document(self, obj):
        sections = []
        for step in obj.answers or []:
            rows = format_html_join('', '<tr><th style="width:32%;vertical-align:top;padding:6px 12px 6px 0;'
                                        'color:#5A5D66;font-weight:600">{}</th><td style="padding:6px 0">{}</td></tr>',
                                    ((item['label'], format_html('{}', linebreaks(item['value'])) if '\n' in item['value']
                                      else item['value']) for item in step['items']))
            sections.append(format_html('<h3 style="margin:18px 0 6px;font-size:15px">{}</h3>'
                                        '<table style="width:100%;border-collapse:collapse">{}</table>',
                                        step['step'], rows))
        return format_html_join('', '{}', ((s,) for s in sections)) or '—'

    def has_add_permission(self, request):
        return False
