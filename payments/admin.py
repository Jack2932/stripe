from django.contrib import admin

from .models import Discount, Item, Order, OrderItem, Tax


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "currency")
    list_filter = ("currency",)
    search_fields = ("name", "description")


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ("name", "stripe_coupon_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "stripe_coupon_id")


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "stripe_tax_rate_id", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "stripe_tax_rate_id")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    autocomplete_fields = ("item",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "currency", "total_price", "discount")
    list_filter = ("created_at", "discount")
    search_fields = ("id", "note")
    inlines = [OrderItemInline]
    filter_horizontal = ("taxes",)
