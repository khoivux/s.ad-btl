from django.db import models
from .product_model import ProductModel

class CosmeticsModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='cosmetics_details')
    brand = models.CharField(max_length=100)
    skin_type = models.CharField(max_length=50, help_text="e.g., Dry, Oily, Sensitive, All")
    is_organic = models.BooleanField(default=False)
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'catalog_cosmetics'

    def __str__(self):
        return f"Cosmetics: {self.product.name} ({self.brand})"
