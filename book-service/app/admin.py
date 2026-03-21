from django.contrib import admin
from .models import Category, Book, Language, BookFormat, Publisher

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(BookFormat)
class BookFormatAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock', 'category', 'language', 'publisher')
    list_filter = ('category', 'language', 'format', 'publisher')
    search_fields = ('title', 'author', 'isbn')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'category', 'price', 'stock', 'image_url')
        }),
        ('Detailed Specs', {
            'fields': ('description', 'page_count', 'isbn', 'published_date', 'language', 'format', 'publisher')
        }),
    )
