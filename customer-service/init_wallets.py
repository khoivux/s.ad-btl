import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_service.settings')
django.setup()

from app.models import Customer, LoyaltyWallet, MembershipLevel

bronze = MembershipLevel.objects.get(name='Bronze')
customers = Customer.objects.all()

for customer in customers:
    wallet, created = LoyaltyWallet.objects.get_or_create(
        customer=customer,
        defaults={'current_level': bronze}
    )
    if created:
        print(f"Created wallet for {customer.email}")
    else:
        print(f"Wallet already exists for {customer.email}")
