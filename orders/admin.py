from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'size', 'color', 'quantity', 'price', 'subtotal']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'total', 'status', 'is_paid', 'created_at']
    list_editable = ['status']
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'phone']
    readonly_fields = ['order_number', 'razorpay_order_id', 'razorpay_payment_id',
                       'razorpay_signature', 'is_paid', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status', 'notes')
        }),
        ('Customer', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Shipping', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_charge', 'discount', 'total')
        }),
        ('Payment', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'is_paid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'used_count', 'max_uses', 'is_active']
    list_editable = ['is_active']
