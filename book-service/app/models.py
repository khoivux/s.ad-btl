from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, blank=True, null=True) # e.g., 'vi', 'en'

    def __str__(self):
        return self.name

class BookFormat(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., Hardcover, Paperback, Ebook

    def __str__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    page_count = models.IntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1543004471-240a0e96bbf4?q=80&w=2670&auto=format&fit=crop')
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    format = models.ForeignKey(BookFormat, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')

    def save(self, *args, **kwargs):
        print(f"[DEBUG] Book.save() called for ID: {self.id} - Title: {self.title}")
        # 1. Standard save to SQL
        super().save(*args, **kwargs)

        # 2. Trigger auto-sync to Catalog (MongoDB)
        from .utils import sync_book_to_catalog
        sync_book_to_catalog(self)

    def delete(self, *args, **kwargs):
        book_id = self.id
        from .utils import delete_book_from_catalog
        # 1. Standard delete from SQL
        super().delete(*args, **kwargs)
        # 2. Remove from catalog
        delete_book_from_catalog(book_id)

    def __str__(self):
        return self.title