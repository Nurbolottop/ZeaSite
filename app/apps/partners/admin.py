"""Технический доступ. Рабочий интерфейс — /hub/candidates/ и /hub/partners/.

Статус в админке только для чтения: менять его можно лишь через
services.change_status() (из интерфейса Hub), чтобы не терять историю.
"""
from django.contrib import admin

from .models import (
    CandidateAssessment, CandidateDecision, Company, CompanyContact, CompanyStatusHistory,
)


class ContactInline(admin.TabularInline):
    model = CompanyContact
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = CompanyStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'changed_at', 'comment')

    def has_add_permission(self, request, obj=None):
        return False


class DecisionInline(admin.TabularInline):
    model = CandidateDecision
    extra = 0
    can_delete = False
    readonly_fields = ('review_date', 'decision', 'comment', 'created_by')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_type', 'industry', 'status', 'manager', 'created_at', 'updated_at')
    list_filter = ('status', 'company_type', 'source', 'manager')
    search_fields = ('name', 'legal_name', 'industry', 'city')
    readonly_fields = ('status', 'status_changed_at', 'created_at', 'updated_at', 'created_by', 'updated_by')
    autocomplete_fields = ('manager',)
    inlines = (ContactInline, DecisionInline, StatusHistoryInline)

    def save_model(self, request, obj, form, change):
        if not change:
            # Новая компания из админки — через сервис, чтобы появилась запись истории
            from .services import create_company
            create_company(company=obj, user=request.user)
            return
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Компании не удаляются; технически — только суперпользователь
        return request.user.is_superuser


@admin.register(CandidateAssessment)
class CandidateAssessmentAdmin(admin.ModelAdmin):
    list_display = ('company', 'mvp_state', 'financial_transparency', 'updated_at')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(CandidateDecision)
class CandidateDecisionAdmin(admin.ModelAdmin):
    list_display = ('company', 'decision', 'review_date', 'created_by')
    list_filter = ('decision',)
    search_fields = ('company__name',)
    readonly_fields = ('company', 'decision', 'review_date', 'comment', 'created_by', 'created_at')

    def has_add_permission(self, request):
        return False  # решения — только через Hub (двигают воронку)


@admin.register(CompanyStatusHistory)
class CompanyStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('company', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',)
    search_fields = ('company__name',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
