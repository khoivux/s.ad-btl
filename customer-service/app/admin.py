from django.contrib import admin
from .models import Customer, Address

class AddressInline(admin.StackedInline):
    model = Address
    extra = 1

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'password')
    search_fields = ('name', 'email')
    inlines = [AddressInline]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'street', 'city', 'country')
