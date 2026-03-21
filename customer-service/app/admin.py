from django.contrib import admin
from .models import Customer, Address, MembershipLevel, LoyaltyWallet, PointTransaction

class AddressInline(admin.StackedInline):
    model = Address
    extra = 1

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email')
    search_fields = ('name', 'email')
    inlines = [AddressInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'street', 'city', 'country')

@admin.register(MembershipLevel)
class MembershipLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'min_points', 'discount_percentage')

@admin.register(LoyaltyWallet)
class LoyaltyWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'usable_points', 'accumulated_points', 'current_level')

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'amount', 'transaction_type', 'description', 'created_at')
