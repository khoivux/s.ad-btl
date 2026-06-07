from django.db import models
from .product_model import ProductModel

class ElectronicsModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='electronics_details')
    brand = models.CharField(max_length=100)
    warranty = models.IntegerField(help_text="Warranty in months")

    class Meta:
        db_table = 'catalog_electronics'

    def __str__(self):
        return f"Electronics: {self.product.name} ({self.brand})"
