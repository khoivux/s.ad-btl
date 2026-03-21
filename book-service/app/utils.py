import requests
import threading
from django.conf import settings

CATALOG_SERVICE_URL = "http://catalog-service:8000"

def _sync_to_catalog_task(book_data):
    """ Task to send book data to MongoDB catalog. """
    try:
        # Corrected URL based on catalog-service urls.py
        requests.post(f"{CATALOG_SERVICE_URL}/sync/", json=book_data, timeout=3)
        print(f"[SYNC] Successfully synced book to catalog.")
    except Exception as e:
        print(f"[SYNC] Error syncing to catalog: {e}")

def sync_book_to_catalog(book_instance):
    """
    Serializes the book instance and triggers the background sync thread.
    Standardizes all FK fields to have '_id' suffix to avoid MongoDB reserved keywords.
    """
    print(f"[DEBUG] Starting sync for book: {book_instance.title} (ID: {book_instance.id})")
    try:
        from .serializers import BookSerializer
        data = BookSerializer(book_instance).data
        
        # Standardize all Foreign Key fields to avoid MongoDB collisions (like 'language')
        fk_fields = ['category', 'language', 'format', 'publisher']
        for field in fk_fields:
            if field in data:
                val = data.pop(field)
                data[f"{field}_id"] = val
            
        print(f"[DEBUG] Serialization & Normalization successful for book ID {book_instance.id}")
        threading.Thread(target=_sync_to_catalog_task, args=(data,)).start()
        print(f"[DEBUG] Sync thread started for book ID {book_instance.id}")
    except Exception as e:
        print(f"[DEBUG] FATAL: Serialization or Threading failed: {e}")

def delete_book_from_catalog(book_id):
    """ Task to remove book from MongoDB catalog. """
    try:
        requests.delete(f"{CATALOG_SERVICE_URL}/sync/{book_id}/", timeout=3)
        print(f"[SYNC] Successfully deleted book from catalog.")
    except Exception as e:
        print(f"[SYNC] Error deleting from catalog: {e}")
