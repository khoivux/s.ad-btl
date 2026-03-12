from django.urls import path
from .views import CartCreate, CartItemView, ViewCart, ClearCart

urlpatterns = [
    path('carts/', CartCreate.as_view(), name='cart-create'),
    path('carts/items/', CartItemView.as_view(), name='cart-item-list'),
    path('carts/items/<int:pk>/', CartItemView.as_view(), name='cart-item-detail'),
    path('carts/<int:customer_id>/', ViewCart.as_view(), name='view-cart'),
    path('carts/<int:customer_id>/clear/', ClearCart.as_view(), name='clear-cart'),
]
