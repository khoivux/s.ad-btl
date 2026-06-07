from django.db import models
from .product_model import ProductModel

class AutoPartsModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='auto_parts_details')
    part_number = models.CharField(max_length=100)
    car_model_compatibility = models.TextField(help_text="Comma separated list of compatible car models")
    warranty_years = models.IntegerField(default=1)

    class Meta:
        db_table = 'catalog_auto_parts'

    def __str__(self):
        return f"AutoPart: {self.product.name} ({self.part_number})"
