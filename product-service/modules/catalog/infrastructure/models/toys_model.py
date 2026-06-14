from django.db import models
from .product_model import ProductModel

class ToysModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='toys_details')
    age_group = models.CharField(max_length=50, help_text="e.g., 0-3, 3+, 12+")
    material = models.CharField(max_length=100)
    requires_batteries = models.BooleanField(default=False)

    class Meta:
        db_table = 'catalog_toys'

    def __str__(self):
        return f"Toy: {self.product.name} ({self.age_group})"
