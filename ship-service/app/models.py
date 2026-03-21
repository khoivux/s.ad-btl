from django.db import models
from datetime import timedelta
from django.utils import timezone
import random
import string

class ShippingMethod(models.Model):
    id_slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_fee = models.FloatField()
    free_threshold = models.FloatField(null=True, blank=True)
    estimated_days = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.name} (${self.base_fee})"

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('ready_for_pickup', 'Ready for Pickup'),
        ('delivering', 'Delivering'),
        ('completed', 'Completed (Delivered)'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.IntegerField(unique=True)
    customer_id = models.IntegerField()
    tracking_code = models.CharField(max_length=50, unique=True, blank=True)
    shipping_method = models.CharField(max_length=50, default='standard')
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ready_for_pickup')
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
