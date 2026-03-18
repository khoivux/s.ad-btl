from django.db import models
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image_url = models.URLField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1543004471-240a0e96bbf4?q=80&w=2670&auto=format&fit=crop')