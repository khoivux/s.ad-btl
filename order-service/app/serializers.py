from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'book_id', 'book_title', 'quantity', 'unit_price', 'subtotal']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'total_amount', 'status', 'shipping_address',
                  'shipping_fee', 'shipping_method', 'created_at', 'updated_at', 'items']
        read_only_fields = ['id', 'created_at', 'updated_at']
