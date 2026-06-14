import requests

PRODUCT_SERVICE_URL = "http://product-service:8000"
CATALOG_SERVICE_URL = "http://catalog-service:8000"

print("Fetching products from product-service...")
r_prod = requests.get(f"{PRODUCT_SERVICE_URL}/products/?page_size=1000", timeout=5)
if r_prod.status_code == 200:
    prod_data = r_prod.json().get('results', [])
    prod_ids = {p['id'] for p in prod_data}
    prod_map = {p['id']: p for p in prod_data}
    print(f"Total products in product-service: {len(prod_ids)}")
else:
    print(f"Failed to fetch from product-service: {r_prod.status_code}")
    prod_ids = set()
    prod_map = {}

print("Fetching products from catalog-service...")
r_cat = requests.get(f"{CATALOG_SERVICE_URL}/products/?page_size=1000", timeout=5)
if r_cat.status_code == 200:
    cat_data = r_cat.json().get('results', [])
    cat_ids = {p['id'] for p in cat_data}
    print(f"Total products in catalog-service: {len(cat_ids)}")
else:
    print(f"Failed to fetch from catalog-service: {r_cat.status_code}")
    cat_ids = set()

# Discrepancies
missing_in_cat = prod_ids - cat_ids
extra_in_cat = cat_ids - prod_ids

print(f"\nDiscrepancy Report:")
print(f"-------------------")
print(f"Products in product-service but missing in catalog-service ({len(missing_in_cat)}):")
for pid in sorted(missing_in_cat):
    print(f"  - ID: {pid}, Name: {prod_map[pid].get('name')}")

print(f"\nProducts in catalog-service but missing in product-service ({len(extra_in_cat)}):")
for pid in sorted(extra_in_cat):
    print(f"  - ID: {pid}")

# Option to sync missing products automatically
if missing_in_cat:
    print(f"\nAttempting to sync missing products to catalog-service...")
    synced_count = 0
    for pid in missing_in_cat:
        prod_info = prod_map[pid]
        # Map fields to match what catalog-service expects (from views.py of catalog-service):
        sync_payload = {
            'id': prod_info['id'],
            'name': prod_info.get('name'),
            'description': prod_info.get('description', ''),
            'price': float(prod_info.get('price', 0)),
            'stock': int(prod_info.get('stock', 0)),
            'image_url': prod_info.get('image_url', ''),
            'category_id': prod_info.get('category_id'),
            'category_name': prod_info.get('category_name', ''),
            'attributes': prod_info.get('attributes', {}),
            'product_type': prod_info.get('product_type', 'General'),
            'domain_data': prod_info.get('domain_data', {})
        }
        r_sync = requests.post(f"{CATALOG_SERVICE_URL}/sync/product/", json=sync_payload, timeout=5)
        if r_sync.status_code == 200:
            print(f"  Synced product ID {pid}: {prod_info.get('name')}")
            synced_count += 1
        else:
            print(f"  Failed to sync ID {pid}: {r_sync.status_code} {r_sync.text}")
    print(f"Successfully synced {synced_count} products.")
