from django.db import models
from .product_model import ProductModel

class FoodModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='food_details')
    expiration_date = models.DateField()
    weight = models.CharField(max_length=50, help_text="e.g., 500g, 1kg")
    is_vegetarian = models.BooleanField(default=False)
    calories = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'catalog_food'

    def __str__(self):
        return f"Food: {self.product.name} (Exp: {self.expiration_date})"
