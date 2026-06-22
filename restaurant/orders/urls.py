from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),
    path('add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart-api/', views.get_cart_json, name='cart_api'),
    path('wishlist-api/', views.get_wishlist_json, name='wishlist_api'),
    path('cart/', views.cart_view, name='cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove-cart/<int:item_id>/', views.remove_from_cart, name='remove_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('Despacito_dashboard_dashboard1234/', views.admin_dashboard, name='admin_dashboard'),
]