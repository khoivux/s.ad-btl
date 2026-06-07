from pymongo import MongoClient
import os

def inspect():
    # Use the exposed port 27018 from docker-compose
    client = MongoClient("mongodb://localhost:27018/")
    db = client['bookstore']
    coll = db['products']
    
    print("--- CATALOG SERVICE (MongoDB) ---")
    print(f"Total products: {coll.count_documents({})}")
    print("\nSample Data (First 5):")
    print("-" * 50)
    for p in coll.find().limit(5):
        print(f"ID: {p.get('sql_book_id')}")
        print(f"Name: {p.get('name')}")
        print(f"Type: {p.get('product_type')}")
        print(f"Domain Data: {p.get('domain_data')}")
        print("-" * 50)

if __name__ == "__main__":
    inspect()
