from django.db import models
from .product_model import ProductModel

class PetSuppliesModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='pet_supplies_details')
    animal_type = models.CharField(max_length=50, help_text="e.g., Dog, Cat, Bird, Fish")
    brand = models.CharField(max_length=100)
    weight_limit = models.FloatField(null=True, blank=True, help_text="in kg")

    class Meta:
        db_table = 'catalog_pet_supplies'

    def __str__(self):
        return f"PetSupply: {self.product.name} for {self.animal_type}"
