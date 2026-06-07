from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('CUSTOMER', 'Customer'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class MembershipLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    min_points = models.IntegerField(default=0)
    discount_percentage = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class LoyaltyWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    usable_points = models.IntegerField(default=0)
    accumulated_points = models.IntegerField(default=0)
    current_level = models.ForeignKey(MembershipLevel, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Wallet for {self.user.username} - {self.usable_points} pts"

class PointTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Earned from purchase'),
        ('SPEND', 'Spent on voucher/reward'),
        ('EXPIRE', 'Expired')
    ]
    wallet = models.ForeignKey(LoyaltyWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} - {self.wallet.user.username}"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100, help_text="Label e.g. 'Home', 'Office'")
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Vietnam')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', 'id']

    def save(self, *args, **kwargs):
        # Only one default address per user
        if self.is_default:
            Address.objects.filter(
                user=self.user, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.name}] {self.street}, {self.city}"