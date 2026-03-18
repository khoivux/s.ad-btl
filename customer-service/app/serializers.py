from rest_framework import serializers
from .models import Customer, Address, MembershipLevel, LoyaltyWallet, PointTransaction

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'customer', 'name', 'recipient_name', 'recipient_phone', 'street', 'city', 'country', 'postal_code', 'is_default']
        read_only_fields = ['id']

class MembershipLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipLevel
        fields = ['id', 'name', 'min_points', 'discount_percentage']

class LoyaltyWalletSerializer(serializers.ModelSerializer):
    current_level = MembershipLevelSerializer(read_only=True)
    
    class Meta:
        model = LoyaltyWallet
        fields = ['id', 'usable_points', 'accumulated_points', 'current_level']

class CustomerSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    wallet = LoyaltyWalletSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone_number', 'addresses', 'wallet']