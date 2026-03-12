from django.urls import path
from .views import ShipmentCreate, ShipmentDetail, ShipmentStatusUpdate, ShippingMethodList, ShipmentByOrder

urlpatterns = [
    path('shipments/', ShipmentCreate.as_view(), name='shipment-list'),
    path('shipments/<int:pk>/', ShipmentDetail.as_view(), name='shipment-detail'),
    path('shipments/order/<int:order_id>/', ShipmentByOrder.as_view(), name='shipment-by-order'),
    path('shipments/<int:pk>/status/', ShipmentStatusUpdate.as_view(), name='shipment-status'),
    path('api/shipping-methods/', ShippingMethodList.as_view(), name='shipping-methods-list'),
]
