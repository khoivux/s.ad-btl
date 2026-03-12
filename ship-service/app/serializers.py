from rest_framework import serializers
from .models import Shipment

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = ['id', 'order_id', 'customer_id', 'tracking_code', 'shipping_method', 'address',
                  'status', 'estimated_delivery', 'created_at', 'updated_at']
        read_only_fields = ['id', 'tracking_code', 'estimated_delivery', 'created_at', 'updated_at']
