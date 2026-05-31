from django.contrib import admin
from .models import ContactMessage


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
