from django.contrib import admin
from django.urls import path
from app.views import (
    CustomerListCreate, CustomerDetail, LoginView, 
    AddressListCreate, AddressDetail, WalletDetail, AddPointsView,
    MembershipLevelList, PointTransactionListView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('customers/', CustomerListCreate.as_view(), name='customer-list'),
    path('customers/<int:pk>/', CustomerDetail.as_view(), name='customer-detail'),
    path('customers/login/', LoginView.as_view(), name='customer-login'),
    path('customers/<int:customer_id>/addresses/', AddressListCreate.as_view(), name='address-list'),
    path('customers/<int:customer_id>/addresses/<int:pk>/', AddressDetail.as_view(), name='address-detail'),
    
    # Loyalty URLs
    path('customers/<int:customer_id>/wallet/', WalletDetail.as_view(), name='wallet-detail'),
    path('customers/<int:customer_id>/wallet/add-points/', AddPointsView.as_view(), name='add-points'),
    path('customers/<int:customer_id>/wallet/transactions/', PointTransactionListView.as_view(), name='point-transactions'),
    path('membership-levels/', MembershipLevelList.as_view(), name='membership-level-list'),
]