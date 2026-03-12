from django.db import models
import uuid

class Payment(models.Model):
    METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOMO', 'MoMo Wallet'),
        ('VNPAY', 'VNPay'),
    ]
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    order_id = models.IntegerField()
    customer_id = models.IntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment #{self.id} - Order {self.order_id} - {self.status}"
