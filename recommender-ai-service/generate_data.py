import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_ecommerce_data(num_users=3000, num_products=200, num_interactions=150000, filename='behavior_dataset.csv'):
    user_ids = [i for i in range(1, num_users + 1)]
    product_ids = [i for i in range(1, num_products + 1)]
    
    # We follow the action types used in the actual microservices logic
    # project behaviors: view, add_to_cart, wishlist, search, rating, comment, purchase, click
    
    start_date = datetime.now() - timedelta(days=60) # Generate 2 months of data
    
    data = []
    
    print(f"\n--- Generating: {filename} ---")
    print(f"Config: {num_users} users, {num_products} products, ~{num_interactions} interactions")
    
    for _ in range(num_interactions // 3): # We generate sequences, so total rows will be around num_interactions
        user = random.choice(user_ids)
        product = random.choice(product_ids)
        
        # Chia nhỏ các loại hành trình người dùng (User Journeys)
        journey = random.choices(
            ['SEARCH', 'BROWSE', 'SAVE', 'BUY_MINIMAL', 'BUY_FULL'], 
            weights=[0.2, 0.3, 0.2, 0.15, 0.15]
        )[0]
        
        base_time = start_date + timedelta(days=random.randint(0, 59), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        if journey == 'SEARCH':
            data.append([user, product, 'search', base_time.isoformat()])
            if random.random() < 0.6: # 60% click vào kết quả tìm kiếm
                base_time += timedelta(seconds=random.randint(5, 20))
                data.append([user, product, 'click', base_time.isoformat()])

        elif journey == 'BROWSE':
            data.append([user, product, 'view', base_time.isoformat()])
            if random.random() < 0.8:
                base_time += timedelta(seconds=random.randint(10, 40))
                data.append([user, product, 'click', base_time.isoformat()])

        elif journey == 'SAVE':
            data.append([user, product, 'view', base_time.isoformat()])
            base_time += timedelta(seconds=random.randint(10, 30))
            data.append([user, product, 'wishlist', base_time.isoformat()])

        elif journey == 'BUY_MINIMAL': # Mua nhanh không đánh giá
            data.append([user, product, 'view', base_time.isoformat()])
            base_time += timedelta(seconds=random.randint(30, 60))
            data.append([user, product, 'add_to_cart', base_time.isoformat()])
            base_time += timedelta(minutes=random.randint(1, 5))
            data.append([user, product, 'purchase', base_time.isoformat()])

        elif journey == 'BUY_FULL': # Mua và để lại feedback đầy đủ
            data.append([user, product, 'view', base_time.isoformat()])
            base_time += timedelta(seconds=random.randint(20, 50))
            data.append([user, product, 'click', base_time.isoformat()])
            base_time += timedelta(seconds=random.randint(30, 90))
            data.append([user, product, 'add_to_cart', base_time.isoformat()])
            base_time += timedelta(minutes=random.randint(2, 10))
            data.append([user, product, 'purchase', base_time.isoformat()])
            # Feedback sau vài ngày
            base_time += timedelta(days=random.randint(2, 7))
            data.append([user, product, 'rating', base_time.isoformat()])
            base_time += timedelta(minutes=random.randint(5, 20))
            data.append([user, product, 'comment', base_time.isoformat()])

    df = pd.DataFrame(data, columns=['user_id', 'product_id', 'action', 'timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Save the dataset
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, 'app', 'ai_core', filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} interaction rows.")
    print(f"Dataset saved to {output_path}")

if __name__ == "__main__":
    # 1. Original Dataset
    generate_ecommerce_data(num_users=3000, num_products=200, num_interactions=150000, filename='behavior_dataset.csv')
    
    # 2. Small Dataset (Fast testing)
    generate_ecommerce_data(num_users=500, num_products=50, num_interactions=20000, filename='behavior_dataset_small.csv')
    
    # 3. Medium Dataset (Balanced)
    generate_ecommerce_data(num_users=1500, num_products=100, num_interactions=70000, filename='behavior_dataset_medium.csv')
    
    # 4. Large Dataset (Stress testing / High quality AI)
    generate_ecommerce_data(num_users=5000, num_products=500, num_interactions=300000, filename='behavior_dataset_large.csv')

