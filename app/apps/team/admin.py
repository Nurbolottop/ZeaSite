from django.contrib import admin

from .models import EmployeeProfile, Specialization


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    """Здесь расширяется список специализаций."""
    list_display = ('name', 'is_technical', 'is_active', 'sort_order')
    list_editable = ('is_technical', 'is_active', 'sort_order')

    def has_delete_permission(self, request, obj=None):
        return False  # на специализацию ссылаются участники проектов — отключайте флажком


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'position', 'employment_type', 'is_active', 'started_at')
    list_filter = ('is_active', 'employment_type', 'specializations')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'position')
    filter_horizontal = ('specializations',)
    autocomplete_fields = ('user',)
