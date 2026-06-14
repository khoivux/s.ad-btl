from django.db import models
from .product_model import ProductModel

class FurnitureModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='furniture_details')
    material = models.CharField(max_length=100, help_text="e.g., Oak, Metal, Plastic")
    dimensions = models.CharField(max_length=100, help_text="e.g., 200x150x50 cm")
    weight_capacity = models.FloatField(null=True, blank=True, help_text="in kg")

    class Meta:
        db_table = 'catalog_furniture'

    def __str__(self):
        return f"Furniture: {self.product.name} ({self.material})"
