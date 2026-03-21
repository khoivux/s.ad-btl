from rest_framework import serializers
from .models import Book, Category, Language, BookFormat, Publisher

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']

class BookFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookFormat
        fields = ['id', 'name']

class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'website']

class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    format_name = serializers.CharField(source='format.name', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'price', 'stock', 
            'page_count', 'isbn', 'published_date', 'image_url', 
            'category', 'category_name', 
            'language', 'language_name',
            'format', 'format_name',
            'publisher', 'publisher_name'
        ]
