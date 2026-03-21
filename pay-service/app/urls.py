from django.urls import path
from .views import PaymentCreate, PaymentDetail, PaymentByOrder

urlpatterns = [
    path('payments/', PaymentCreate.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetail.as_view(), name='payment-detail'),
    path('payments/order/<int:order_id>/', PaymentByOrder.as_view(), name='payment-by-order'),
]
