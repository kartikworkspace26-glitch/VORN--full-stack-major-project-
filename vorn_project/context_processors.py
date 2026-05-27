from django.conf import settings


def vorn_globals(request):
    """Pass global VORN constants and computed values to all templates."""
    from store.models import Category
    from accounts.models import Wishlist

    # Active categories for mega-menu
    try:
        nav_categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')[:12]
    except Exception:
        nav_categories = []

    # Wishlist count from DB (if authenticated) or session (if not)
    wishlist_count = 0
    if request.user.is_authenticated:
        try:
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
        except Exception:
            wishlist_count = len(request.session.get('wishlist', []))
    else:
        wishlist_count = len(request.session.get('wishlist', []))

    return {
        'nav_categories': nav_categories,
        'wishlist_count': wishlist_count,
        'VORN_CURRENCY_SYMBOL': getattr(settings, 'VORN_CURRENCY_SYMBOL', '₹'),
        'VORN_FREE_SHIPPING_THRESHOLD': getattr(settings, 'VORN_FREE_SHIPPING_THRESHOLD', 999),
        'VORN_SITE_NAME': getattr(settings, 'VORN_SITE_NAME', 'VORN'),
        'VORN_TAGLINE': getattr(settings, 'VORN_TAGLINE', 'Refined Luxury Fashion'),
        'VORN_SUPPORT_EMAIL': getattr(settings, 'VORN_SUPPORT_EMAIL', 'hello@vorn.in'),
    }
