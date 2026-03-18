import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'book_service.settings')
django.setup()

from app.models import Book

def seed_images():
    # A set of beautiful book covers from Unsplash
    images = [
        "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=2574&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1543004471-240a0e96bbf4?q=80&w=2670&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1512820790803-83ca734da794?q=80&w=2698&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1589998059171-988d887df646?q=80&w=2676&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1532012197267-da84d127e765?q=80&w=2574&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?q=80&w=2673&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1510172951991-859a69907ac4?q=80&w=2574&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1541963463532-d68292c34b19?q=80&w=2576&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1516979187457-637abb4f9353?q=80&w=2670&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1476275466078-4007374efbbe?q=80&w=2529&auto=format&fit=crop"
    ]

    books = Book.objects.all()
    print(f"Seeding images for {books.count()} books...")
    
    for i, book in enumerate(books):
        img_url = images[i % len(images)]
        book.image_url = img_url
        book.save()
        print(f"Updated: {book.title} -> {img_url}")

if __name__ == "__main__":
    seed_images()
