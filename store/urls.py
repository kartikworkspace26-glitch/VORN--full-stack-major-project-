from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('shop/', views.catalog, name='catalog'),
    path('shop/search/', views.search, name='search'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:key>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<str:key>/', views.update_cart, name='update_cart'),

    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Reviews
    path('review/<int:product_id>/', views.submit_review, name='submit_review'),
]
