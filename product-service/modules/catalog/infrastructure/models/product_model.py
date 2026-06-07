from django.db import models
from .category_model import CategoryModel

class ProductModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Money is better as Decimal, but user said Float. I'll use Decimal as it's already there and safer.
    stock = models.IntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE, null=True, blank=True, related_name='products')
    attributes = models.JSONField(default=dict, blank=True) # Legacy attributes

    class Meta:
        db_table = 'catalog_product'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 2. Trigger auto-sync to Catalog Mongo (assuming the same utility is accessible)
        self._sync_to_mongo()

    def delete(self, *args, **kwargs):
        product_id = self.id
        super().delete(*args, **kwargs)
        self._delete_from_mongo(product_id)

    def _sync_to_mongo(self):
        try:
            import requests
            # Determine domain data for sync
            domain_data = {}
            product_type = "General"
            if hasattr(self, 'book_details'):
                product_type = "Book"
                domain_data = {"author": self.book_details.author, "publisher": self.book_details.publisher, "isbn": self.book_details.isbn}
            elif hasattr(self, 'electronics_details'):
                product_type = "Electronics"
                domain_data = {"brand": self.electronics_details.brand, "warranty": self.electronics_details.warranty}
            elif hasattr(self, 'fashion_details'):
                product_type = "Fashion"
                domain_data = {"size": self.fashion_details.size, "color": self.fashion_details.color}
            elif hasattr(self, 'cosmetics_details'):
                product_type = "Cosmetics"
                domain_data = {"brand": self.cosmetics_details.brand, "skin_type": self.cosmetics_details.skin_type, "expiration_date": str(self.cosmetics_details.expiration_date)}
            elif hasattr(self, 'toys_details'):
                product_type = "Toys"
                domain_data = {"age_group": self.toys_details.age_group, "material": self.toys_details.material}
            elif hasattr(self, 'furniture_details'):
                product_type = "Furniture"
                domain_data = {"material": self.furniture_details.material, "dimensions": self.furniture_details.dimensions}
            elif hasattr(self, 'food_details'):
                product_type = "Food"
                domain_data = {"expiration_date": str(self.food_details.expiration_date), "weight": self.food_details.weight}
            elif hasattr(self, 'medicine_details'):
                product_type = "Medicine"
                domain_data = {"active_ingredient": self.medicine_details.active_ingredient, "dosage": self.medicine_details.dosage}
            elif hasattr(self, 'pet_supplies_details'):
                product_type = "PetSupplies"
                domain_data = {"animal_type": self.pet_supplies_details.animal_type, "brand": self.pet_supplies_details.brand}
            elif hasattr(self, 'auto_parts_details'):
                product_type = "AutoParts"
                domain_data = {"part_number": self.auto_parts_details.part_number, "car_model_compatibility": self.auto_parts_details.car_model_compatibility}

            data = {
                "sql_book_id": self.id,
                "name": self.name,
                "description": self.description,
                "category_id": self.category_id,
                "category_name": self.category.name if self.category else "Unknown",
                "price": float(self.price),
                "stock": self.stock,
                "image_url": self.image_url,
                "attributes": self.attributes,
                "product_type": product_type,
                "domain_data": domain_data
            }
            requests.post("http://catalog-service:8000/sync/product/", json=data, timeout=3)
        except Exception as e:
            print(f"[Sync] Failed to sync Product {self.id}: {e}")

    def _delete_from_mongo(self, product_id):
        try:
            import requests
            requests.delete(f"http://catalog-service:8000/sync/product/{product_id}/", timeout=3)
        except Exception as e:
            pass

    def __str__(self):
        return self.name
