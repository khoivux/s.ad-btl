from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipping', 'Shipping'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    customer_id = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField(blank=True, default='')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_method = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book_id = models.IntegerField()
    book_title = models.CharField(max_length=255, default='')  # Snapshot
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot price

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"OrderItem #{self.id} - Book {self.book_id} x{self.quantity}"
