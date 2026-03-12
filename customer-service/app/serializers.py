from rest_framework import serializers
from .models import Customer, Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'customer', 'name', 'street', 'city', 'country', 'postal_code', 'is_default']
        read_only_fields = ['id']

class CustomerSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number', 'addresses']