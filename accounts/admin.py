from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Address, Wishlist, NewsletterSubscriber


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['phone', 'gender', 'date_of_birth', 'avatar', 'loyalty_points', 'email_verified']


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ['label', 'full_name', 'city', 'state', 'pincode', 'is_default']


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, AddressInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']


# Re-register User with enhanced admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'state', 'label', 'is_default']
    list_filter = ['label', 'state', 'is_default']
    search_fields = ['user__username', 'full_name', 'city']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_at']
    list_filter = ['added_at']


@admin.register(NewsletterSubscriber)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'subscribed_at', 'is_active']
    list_editable = ['is_active']
    search_fields = ['email', 'name']
