from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'item_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone')
    inlines = [OrderItemInline]
    readonly_fields = ('total_price', 'created_at')

admin.site.register(Category)
admin.site.register(MenuItem)