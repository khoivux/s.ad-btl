from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    password = models.CharField(max_length=255, default='123456')

    def __str__(self):
        return f"{self.name} ({self.email})"

class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100, help_text="Label e.g. 'Home', 'Office'")
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Vietnam')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', 'id']

    def save(self, *args, **kwargs):
        # Only one default address per customer
        if self.is_default:
            Address.objects.filter(
                customer=self.customer, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.name}] {self.street}, {self.city}"