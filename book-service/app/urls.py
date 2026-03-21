from django.urls import path
from .views import BookListCreate, BookDetail, BookInventoryUpdate, CategoryListCreate, CategoryDetail

urlpatterns = [
    path('books/', BookListCreate.as_view(), name='book-list'),
    path('books/<int:pk>/', BookDetail.as_view(), name='book-detail'),
    path('books/<int:pk>/inventory/', BookInventoryUpdate.as_view(), name='book-inventory-update'),
    path('categories/', CategoryListCreate.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetail.as_view(), name='category-detail'),
]
