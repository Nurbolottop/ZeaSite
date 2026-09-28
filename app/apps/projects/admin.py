"""Технический доступ. Рабочий интерфейс — /hub/projects/.

Статус, компания, договор, PM и технический руководитель — только для чтения:
они меняются через services (проверка ролей, история). Создания проектов и
добавления участников в админке нет — только через Hub.
"""
from django.contrib import admin

from .models import Project, ProjectMember, ProjectStatusHistory, ProjectTechnicalInfo


class MemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0
    can_delete = False
    fields = ('member', 'specialization', 'joined_at', 'left_at', 'is_active', 'note')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class StatusHistoryInline(admin.TabularInline):
    model = ProjectStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'changed_at', 'comment')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'company', 'status', 'priority', 'pm', 'technical_lead', 'planned_end_date')
    list_filter = ('status', 'project_type', 'priority')
    search_fields = ('code', 'name', 'company__name')
    readonly_fields = ('company', 'contract', 'status', 'paused_from_status', 'status_changed_at',
                       'launch_date', 'pm', 'technical_lead', 'created_at', 'updated_at',
                       'created_by', 'updated_by')
    inlines = (MemberInline, StatusHistoryInline)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProjectTechnicalInfo)
class ProjectTechnicalInfoAdmin(admin.ModelAdmin):
    """Форма админки вызывает model.clean() — проверка на секреты работает и здесь."""
    list_display = ('project', 'repository_url', 'production_url', 'updated_at')
    readonly_fields = ('project', 'created_at', 'updated_at', 'created_by', 'updated_by')

    def has_add_permission(self, request):
        return False


@admin.register(ProjectStatusHistory)
class ProjectStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('project', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('member', 'project', 'specialization', 'joined_at', 'left_at', 'is_active')
    list_filter = ('is_active', 'specialization')
    readonly_fields = ('project', 'member', 'specialization', 'joined_at', 'left_at', 'is_active', 'added_by')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
