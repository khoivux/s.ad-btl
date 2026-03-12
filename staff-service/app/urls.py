from django.urls import path
from .views import StaffBookManager, StaffBookDetailManager, StaffLogin

urlpatterns = [
    path('staff/login/', StaffLogin.as_view(), name='staff-login'),
    path('staff/books/', StaffBookManager.as_view(), name='staff-books'),
    path('staff/books/<int:pk>/', StaffBookDetailManager.as_view(), name='staff-books-detail'),
]
