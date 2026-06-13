from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('shop/', views.catalog, name='catalog'),
    path('shop/men/', views.men_catalog, name='men_catalog'),
    path('shop/women/', views.women_catalog, name='women_catalog'),
    path('shop/search/', views.search, name='search'),
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('lookbook/', views.lookbook, name='lookbook'),
    path('size-guide/', views.size_guide, name='size_guide'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/json/', views.cart_json_view, name='cart_json'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:key>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<str:key>/', views.update_cart, name='update_cart'),

    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    # Reviews
    path('review/<int:product_id>/', views.submit_review, name='submit_review'),

    # Contact Us
    path('contact/', views.contact_view, name='contact'),

    # Legal / Terms
    path('legal/', views.legal_view, name='legal'),

    # AI Stylist Chatbot API
    path('api/ai-stylist/', views.ai_stylist, name='ai_stylist'),
]
