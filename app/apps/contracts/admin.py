"""Технический доступ. Рабочий интерфейс — /hub/contracts/.

Статус, файлы и история — только для чтения: статус меняется через
services.change_contract_status(), файлы загружаются через Hub с проверкой.
У приватных файлов нет URL, поэтому в админке выводится только имя.
"""
from django.contrib import admin

from .models import Contract, ContractDocument, ContractStatusHistory


class DocumentInline(admin.TabularInline):
    model = ContractDocument
    extra = 0
    can_delete = False
    fields = ('document_type', 'title', 'original_name', 'size', 'uploaded_by', 'uploaded_at')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class StatusHistoryInline(admin.TabularInline):
    model = ContractStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'changed_at', 'comment')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'company', 'status', 'share_percent', 'start_date', 'end_date', 'created_by')
    list_filter = ('status', 'calculation_base_type')
    search_fields = ('number', 'title', 'company__name')
    exclude = ('file',)
    readonly_fields = ('company', 'status', 'status_changed_at', 'file_original_name', 'file_uploaded_at',
                       'created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = (DocumentInline, StatusHistoryInline)

    def has_add_permission(self, request):
        return False  # договоры создаются в Hub (черновик + история)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContractDocument)
class ContractDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'contract', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type',)
    search_fields = ('title', 'contract__number', 'contract__company__name')
    exclude = ('file',)
    readonly_fields = ('uid', 'contract', 'original_name', 'size', 'uploaded_by', 'uploaded_at')

    def has_add_permission(self, request):
        return False


@admin.register(ContractStatusHistory)
class ContractStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('contract', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
