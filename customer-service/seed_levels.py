import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_service.settings')
django.setup()

from app.models import MembershipLevel

levels = [
    {'name': 'Bronze', 'min_points': 0, 'discount_percentage': 0},
    {'name': 'Silver', 'min_points': 500, 'discount_percentage': 5},
    {'name': 'Gold', 'min_points': 2000, 'discount_percentage': 10},
    {'name': 'Platinum', 'min_points': 10000, 'discount_percentage': 15},
]

for lvl in levels:
    obj, created = MembershipLevel.objects.update_or_create(
        name=lvl['name'],
        defaults={'min_points': lvl['min_points'], 'discount_percentage': lvl['discount_percentage']}
    )
    if created:
        print(f"Created level: {lvl['name']}")
    else:
        print(f"Updated level: {lvl['name']}")
