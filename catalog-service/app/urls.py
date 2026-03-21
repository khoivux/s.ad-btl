from django.urls import path
from .views import CatalogSyncView, CatalogDeleteSyncView, CatalogListView, CatalogDetailView, CatalogCategorySyncView

urlpatterns = [
    path('sync/', CatalogSyncView.as_view(), name='catalog-sync'),
    path('sync/<int:book_id>/', CatalogDeleteSyncView.as_view(), name='catalog-delete-sync'),
    path('sync/category/<int:category_id>/', CatalogCategorySyncView.as_view(), name='catalog-category-sync'),
    path('search/', CatalogListView.as_view(), name='catalog-list'),
    path('books/', CatalogListView.as_view(), name='catalog-books'),
    path('books/<int:book_id>/', CatalogDetailView.as_view(), name='catalog-detail'),
]
