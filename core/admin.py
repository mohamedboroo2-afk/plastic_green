from django.contrib import admin
from .models import Participant, Tree, Sale, SaleTree, TreeRequest, ExpenseCategory, SaleExpense


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'join_date', 'is_active']
    list_filter = ['is_active', 'join_date']
    search_fields = ['name', 'phone']


@admin.register(Tree)
class TreeAdmin(admin.ModelAdmin):
    list_display = ['tree_type', 'description', 'created_at']
    search_fields = ['tree_type']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_date', 'weight_kg', 'total_price']
    list_filter = ['sale_date']
    readonly_fields = ['total_price']


@admin.register(SaleTree)
class SaleTreeAdmin(admin.ModelAdmin):
    list_display = ['sale', 'tree', 'quantity', 'price_per_tree']


@admin.register(SaleExpense)
class SaleExpenseAdmin(admin.ModelAdmin):
    list_display = ['sale', 'category', 'quantity', 'price_per_unit']


@admin.register(TreeRequest)
class TreeRequestAdmin(admin.ModelAdmin):
    list_display = ['participant', 'tree', 'quantity', 'position', 'status', 'delivery_number', 'request_date']
    list_filter = ['status', 'request_date']
    search_fields = ['participant__name', 'tree__tree_type', 'delivery_number']
    readonly_fields = ['position', 'delivery_number']