from django.urls import path
from .views import (
    OrderListCreate, OrderDetail, OrderStatusUpdate, 
    CheckPurchase, OrderCancelView, OrderDeleteView,
    VoucherList, VoucherDetail, 
    StaffVoucherListCreate, StaffVoucherDetail,
    RedeemVoucher, CustomerVouchersView
)

urlpatterns = [
    path('orders/', OrderListCreate.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetail.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdate.as_view(), name='order-status'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order-delete'),
    path('api/check-purchase/', CheckPurchase.as_view(), name='check-purchase'),
    
    # Customer Voucher URLs
    path('vouchers/', VoucherList.as_view(), name='voucher-list'),
    path('vouchers/<str:code>/', VoucherDetail.as_view(), name='voucher-detail'),
    path('vouchers/customer/<int:customer_id>/', CustomerVouchersView.as_view(), name='customer-vouchers'),
    path('vouchers/redeem/', RedeemVoucher.as_view(), name='voucher-redeem'),

    # Staff Voucher URLs (Internal)
    path('staff/vouchers/', StaffVoucherListCreate.as_view(), name='staff-voucher-list'),
    path('staff/vouchers/<int:pk>/', StaffVoucherDetail.as_view(), name='staff-voucher-detail'),
]
