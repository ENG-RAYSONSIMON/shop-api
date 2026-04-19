from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'status', 'total_price', 'ordered_at')
    list_filter = ('status', 'ordered_at')
    search_fields = ('user__username', 'product__name')
    ordering = ('-ordered_at',)
