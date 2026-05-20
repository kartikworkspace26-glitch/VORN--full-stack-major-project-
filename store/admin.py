from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVariant, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 5
    fields = ['size', 'color', 'stock', 'sku']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'compare_price', 'gender',
                    'is_featured', 'is_new_arrival', 'is_active', 'stock']
    list_editable = ['price', 'is_featured', 'is_new_arrival', 'is_active', 'stock']
    list_filter = ['category', 'gender', 'is_featured', 'is_new_arrival', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'gender', 'short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price')
        }),
        ('Details', {
            'fields': ('material', 'care_instructions', 'stock')
        }),
        ('Visibility', {
            'fields': ('is_featured', 'is_new_arrival', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_verified', 'created_at']
    list_editable = ['is_verified']
    list_filter = ['rating', 'is_verified']


admin.site.site_header = 'VORN Administration'
admin.site.site_title = 'VORN Admin'
admin.site.index_title = 'VORN Fashion Platform'
