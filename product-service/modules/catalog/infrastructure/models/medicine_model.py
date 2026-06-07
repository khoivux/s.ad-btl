from django.db import models
from .product_model import ProductModel

class MedicineModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='medicine_details')
    active_ingredient = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100, help_text="e.g., 500mg, 10ml")
    prescription_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'catalog_medicine'

    def __str__(self):
        return f"Medicine: {self.product.name} ({self.active_ingredient})"
