import os
import sys
import django
import requests

# Set up django context
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender_ai_service.settings')
django.setup()

from app.ai_core.neo4j_db import neo4j_db

user_id = 3
print(f"=== Syncing data to Neo4j for user_id={user_id} (customer@example.com) ===")

def ensure_product_in_neo4j(product_id):
    try:
        r = requests.get(f"http://catalog-service:8000/products/{product_id}/", timeout=2)
        if r.status_code == 200:
            p = r.json()
            title = p.get('name') or p.get('title')
            category = p.get('category_name', 'General')
            if title:
                neo4j_db.merge_product(product_id, title, category)
                return True
    except Exception as e:
        print(f"  Error fetching product {product_id} details: {e}")
    return False

# 1. Sync MongoDB Interactions
print("\nFetching logs from interaction-service...")
try:
    r_logs = requests.get(f"http://interaction-service:8000/logs/user/{user_id}/", timeout=5)
    if r_logs.status_code == 200:
        logs = r_logs.json()
        print(f"Found {len(logs)} interaction logs in MongoDB.")
        sync_count = 0
        for log in logs:
            action = log.get('action') or log.get('action_type')
            product_id = log.get('product_id') or log.get('book_id')
            if action and product_id:
                product_id = int(product_id)
                # Ensure product exists in Neo4j with a name
                ensure_product_in_neo4j(product_id)
                # Map actions
                action_clean = action.lower().replace('_product', '')
                neo4j_db.record_interaction(user_id, product_id, action_clean)
                print(f"  Recorded Interaction: User {user_id} -{action_clean}-> Product {product_id}")
                sync_count += 1
        print(f"Successfully synced {sync_count} interactions from MongoDB.")
    else:
        print(f"Failed to fetch logs: {r_logs.status_code}")
except Exception as e:
    print(f"Error syncing MongoDB logs: {e}")

# 2. Sync Purchase History from order-service
print("\nFetching orders from order-service...")
try:
    r_orders = requests.get(f"http://order-service:8000/orders/", timeout=5)
    if r_orders.status_code == 200:
        orders_data = r_orders.json()
        orders = orders_data.get('results', []) if isinstance(orders_data, dict) else orders_data
        
        user_orders = [o for o in orders if o.get('customer_id') == user_id]
        print(f"Found {len(user_orders)} orders for user_id={user_id} in MySQL.")
        
        order_sync_count = 0
        for o in user_orders:
            order_id = o['id']
            # Fetch order details to get items
            r_items = requests.get(f"http://order-service:8000/orders/{order_id}/", timeout=5)
            if r_items.status_code == 200:
                items = r_items.json().get('items', [])
                for item in items:
                    product_id = item.get('product_id') or item.get('book_id')
                    if product_id:
                        product_id = int(product_id)
                        ensure_product_in_neo4j(product_id)
                        neo4j_db.record_interaction(user_id, product_id, 'purchase')
                        print(f"  Recorded Purchase: User {user_id} -purchase-> Product {product_id}")
                        order_sync_count += 1
        print(f"Successfully synced {order_sync_count} purchased items from order-service.")
    else:
        print(f"Failed to fetch orders: {r_orders.status_code}")
except Exception as e:
    print(f"Error syncing orders: {e}")

print("\n=== Sync completed ===")
