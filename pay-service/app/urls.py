from django.urls import path
from .views import PaymentCreate, PaymentDetail

urlpatterns = [
    path('payments/', PaymentCreate.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentDetail.as_view(), name='payment-detail'),
]
