import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
django.setup()

from app.models import User

# Create Admin
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'role': 'ADMIN',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("Admin created: admin/admin123")
else:
    print("Admin already exists")

# Create Staff
staff_user, created = User.objects.get_or_create(
    username='staff',
    defaults={
        'email': 'staff@example.com',
        'role': 'STAFF'
    }
)
if created:
    staff_user.set_password('staff123')
    staff_user.save()
    print("Staff created: staff/staff123")
else:
    print("Staff already exists")

# Create Customer
customer_user, created = User.objects.get_or_create(
    username='customer',
    defaults={
        'email': 'customer@example.com',
        'role': 'CUSTOMER'
    }
)
if created:
    customer_user.set_password('customer123')
    customer_user.save()
    print("Customer created: customer/customer123")
else:
    print("Customer already exists")
