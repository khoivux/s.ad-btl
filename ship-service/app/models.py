from django.db import models
from datetime import timedelta
from django.utils import timezone
import random
import string

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting (Pending processing)'),
        ('packing', 'Packing (Preparing your order)'),
        ('in_transit', 'In Transit (Shipping)'),
        ('delivered', 'Delivered (Successfully handed over)'),
        ('cancelled', 'Cancelled'),
    ]
    METHOD_CHOICES = [
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
    ]
    
    order_id = models.IntegerField(unique=True)
    customer_id = models.IntegerField()
    tracking_code = models.CharField(max_length=50, unique=True, blank=True)
    shipping_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='standard')
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            chars = string.ascii_uppercase + string.digits
            prefix = "EX" if self.shipping_method == 'express' else "ST"
            self.tracking_code = f"VN-{prefix}-" + ''.join(random.choices(chars, k=8))
        if not self.estimated_delivery:
            days = random.randint(1, 2) if self.shipping_method == 'express' else random.randint(3, 5)
            self.estimated_delivery = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment #{self.id} - Order {self.order_id} - {self.tracking_code} ({self.shipping_method})"
