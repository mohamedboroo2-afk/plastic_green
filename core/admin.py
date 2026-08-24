from django.contrib import admin
from .models import Participant, Tree, Sale, SaleTree, TreeRequest

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'join_date', 'is_active']
    list_filter = ['is_active', 'join_date']
    search_fields = ['name', 'phone']

@admin.register(Tree)
class TreeAdmin(admin.ModelAdmin):
    list_display = ['tree_type', 'description', 'created_at']  # تم تغيير name إلى tree_type
    list_filter = ['tree_type']
    search_fields = ['tree_type']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_date', 'weight_kg', 'total_price', 'participant']
    list_filter = ['sale_date']
    search_fields = ['participant__name']
    readonly_fields = ['total_price']

@admin.register(SaleTree)
class SaleTreeAdmin(admin.ModelAdmin):
    list_display = ['sale', 'tree', 'quantity', 'price_per_tree']
    list_filter = ['sale__sale_date']
    search_fields = ['tree__tree_type']

@admin.register(TreeRequest)
class TreeRequestAdmin(admin.ModelAdmin):
    list_display = ['participant', 'tree', 'quantity', 'position', 'status', 'request_date']
    list_filter = ['status', 'request_date']
    search_fields = ['participant__name', 'tree__tree_type']
    readonly_fields = ['position']