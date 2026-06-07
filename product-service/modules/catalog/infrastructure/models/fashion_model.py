from django.db import models
from .product_model import ProductModel

class FashionModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='fashion_details')
    size = models.CharField(max_length=10)
    color = models.CharField(max_length=50)

    class Meta:
        db_table = 'catalog_fashion'

    def __str__(self):
        return f"Fashion: {self.product.name} ({self.size}, {self.color})"
