from django.contrib import admin
from django.urls import path
from app.views import (
    UserListCreate, UserDetail, LoginView, 
    AddressListCreate, AddressDetail, WalletDetail, AddPointsView,
    PointTransactionListView, MembershipLevelList,
    StaffProductManager, StaffProductDetailManager
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', UserListCreate.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('users/login/', LoginView.as_view(), name='user-login'),
    path('users/<int:user_id>/addresses/', AddressListCreate.as_view(), name='address-list'),
    path('users/<int:user_id>/addresses/<int:pk>/', AddressDetail.as_view(), name='address-detail'),
    
    # Loyalty URLs
    path('users/<int:user_id>/wallet/', WalletDetail.as_view(), name='wallet-detail'),
    path('users/<int:user_id>/wallet/add-points/', AddPointsView.as_view(), name='add-points'),
    path('users/<int:user_id>/wallet/transactions/', PointTransactionListView.as_view(), name='point-transactions'),
    path('membership-levels/', MembershipLevelList.as_view(), name='membership-level-list'),

    # Staff Specific (Proxy)
    path('staff/products/', StaffProductManager.as_view(), name='staff-product-list'),
    path('staff/products/<int:pk>/', StaffProductDetailManager.as_view(), name='staff-product-detail'),
]