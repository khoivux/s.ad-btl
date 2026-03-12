from django.urls import path
from .views import OrderListCreate, OrderDetail, OrderStatusUpdate, CheckPurchase

urlpatterns = [
    path('orders/', OrderListCreate.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdate.as_view(), name='order-status'),
    path('api/check-purchase/', CheckPurchase.as_view(), name='check-purchase'),
]
