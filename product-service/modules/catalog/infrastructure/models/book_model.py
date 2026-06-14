from django.db import models
from .product_model import ProductModel

class BookModel(models.Model):
    product = models.OneToOneField(ProductModel, on_delete=models.CASCADE, related_name='book_details')
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20)

    class Meta:
        db_table = 'catalog_book'

    def __str__(self):
        return f"Book: {self.product.name} by {self.author}"
