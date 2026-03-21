#!/bin/bash
python manage.py migrate
cat <<EOF | python manage.py shell
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', '123')
print("Superuser matched or created successfully.")
EOF
