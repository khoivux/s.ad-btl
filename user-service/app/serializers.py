from rest_framework import serializers
from .models import User, Address, MembershipLevel, LoyaltyWallet, PointTransaction

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user', 'name', 'recipient_name', 'recipient_phone', 'street', 'city', 'country', 'postal_code', 'is_default']
        read_only_fields = ['id']

class MembershipLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipLevel
        fields = ['id', 'name', 'min_points', 'discount_percentage']

class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ['id', 'amount', 'transaction_type', 'description', 'created_at']

class LoyaltyWalletSerializer(serializers.ModelSerializer):
    current_level = MembershipLevelSerializer(read_only=True)
    transactions = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyWallet
        fields = ['id', 'usable_points', 'accumulated_points', 'current_level', 'transactions']

    def get_transactions(self, obj):
        txns = obj.transactions.all().order_by('-created_at')[:20]  # Get last 20
        return PointTransactionSerializer(txns, many=True).data


class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    wallet = LoyaltyWalletSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'role', 'addresses', 'wallet', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_staff', 'is_superuser']