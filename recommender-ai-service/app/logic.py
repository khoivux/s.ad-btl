import requests
import json
from django.conf import settings

BOOK_SERVICE_URL = "http://book-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"

def get_recommendations(customer_id=None):
    """ Main function to generate recommendations based on weights and logic. """
    books = []
    try:
        # 1. Fetch all books from Book Service
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        if r.status_code == 200:
            books = r.json()
    except Exception as e:
        print(f"[RECOM] Error fetching books: {e}")
        return []

    if not books: return []

    # 2. Calculate Bayesian Average for each book (Global Quality)
    # R = average rating of book
    # v = number of reviews for the book
    # m = min reviews required to be listed (e.g., 1)
    # C = mean rating across whole report
    all_ratings = [b.get('average_rating', 0) for b in books if b.get('reviews_count', 0) > 0]
    C = sum(all_ratings) / len(all_ratings) if all_ratings else 0
    m = 1
    
    for book in books:
        v = book.get('reviews_count', 0)
        R = book.get('average_rating', 0)
        if v + m > 0:
            book['bayesian_score'] = (v / (v + m)) * R + (m / (v + m)) * C
        else:
            book['bayesian_score'] = 0

    # 3. Personalization Logic
    user_prefs = {'genres': {}, 'authors': {}}
    purchased_book_ids = []

    if customer_id:
        try:
            # Fetch user orders to identify tastes
            or_r = requests.get(f"{ORDER_SERVICE_URL}/orders/?customer_id={customer_id}")
            if or_r.status_code == 200:
                orders = or_r.json()
                for order in orders:
                    # Collect item data from orders
                    for item in order.get('items', []):
                        book_id = item.get('book_id')
                        purchased_book_ids.append(book_id)
                        
                        # Fetch specific book details to get category/author
                        # (Optimized: we could cache these in a real system)
                        br = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/")
                        if br.status_code == 200:
                            b_info = br.json()
                            genre = b_info.get('category_name', 'General')
                            author = b_info.get('author', 'Unknown')
                            
                            user_prefs['genres'][genre] = user_prefs['genres'].get(genre, 0) + 1
                            user_prefs['authors'][author] = user_prefs['authors'].get(author, 0) + 1
        except Exception as e:
            print(f"[RECOM] Error fetching user data: {e}")

    # 4. Final Scoring Function
    scored_books = []
    for book in books:
        # Skip items already bought
        if book['id'] in purchased_book_ids:
            continue
            
        final_score = book['bayesian_score']
        
        # Boost based on history
        genre = book.get('category_name')
        author = book.get('author')
        
        # Bonus for genres you like (+50% weight)
        if genre in user_prefs['genres']:
            final_score += user_prefs['genres'][genre] * 0.5
            
        # Bonus for authors you like (+30% weight)
        if author in user_prefs['authors']:
            final_score += user_prefs['authors'][author] * 0.3

        book['final_score'] = final_score
        scored_books.append(book)

    # 5. Sort by final score and return top IDs
    scored_books.sort(key=lambda x: x['final_score'], reverse=True)
    return scored_books[:5]
