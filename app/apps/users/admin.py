from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import HubProfile

User = get_user_model()


class HubProfileInline(admin.StackedInline):
    model = HubProfile
    can_delete = False
    verbose_name_plural = 'Профиль сотрудника ZEA Hub'
    fields = ('phone', 'avatar')


# Расширяем стандартную админку auth.User (модель не меняется)
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (HubProfileInline,)
    list_display = (
        'username', 'full_name', 'email', 'roles_display',
        'is_active', 'is_staff', 'is_superuser', 'last_login',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'hub_profile__phone')
    actions = ('activate_users', 'deactivate_users')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'email')}),
        ('Роли и доступ', {'fields': ('is_active', 'groups', 'is_staff', 'is_superuser')}),
        ('Индивидуальные права', {'classes': ('collapse',), 'fields': ('user_permissions',)}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'usable_password', 'password1', 'password2'),
        }),
        ('Личные данные', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Роли и доступ', {
            'classes': ('wide',),
            'fields': ('is_active', 'groups'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('groups')

    @admin.display(description='Имя', ordering='last_name')
    def full_name(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Роли')
    def roles_display(self, obj):
        # prefetch groups → без доп. запросов
        return ', '.join(g.name for g in obj.groups.all()) or '—'

    @admin.action(description='Активировать выбранных пользователей')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано: {updated}', messages.SUCCESS)

    @admin.action(description='Деактивировать выбранных пользователей')
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f'Деактивировано: {updated}', messages.SUCCESS)
