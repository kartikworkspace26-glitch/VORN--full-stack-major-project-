from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('pay/', views.initiate_payment_link, name='initiate_payment_link'),
    path('confirm/<str:order_number>/', views.confirm_payment, name='confirm_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    path('history/', views.order_history, name='order_history'),
    path('detail/<str:order_number>/', views.order_detail, name='order_detail'),
]
