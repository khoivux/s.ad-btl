import pandas as pd
import os
import sys

# Thêm đường dẫn để import được neo4j_db
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Giả lập môi trường Django settings để import neo4j_db
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender_ai_service.settings')
try:
    django.setup()
except:
    pass

from app.ai_core.neo4j_db import neo4j_db

def seed_graph():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ai_core', 'behavior_dataset.csv')
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found!")
        return

    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Xóa dữ liệu cũ để làm sạch KB
    print("Cleaning old graph data...")
    with neo4j_db.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # Map action strings to Neo4j Relationship Types
    action_map = {
        'view': 'VIEWED', 'click': 'CLICKED', 'wishlist': 'WISHLISTED',
        'add_to_cart': 'ADDED_TO_CART', 'purchase': 'PURCHASED',
        'search': 'SEARCHED', 'rating': 'RATED', 'comment': 'COMMENTED'
    }

    print(f"Seeding {len(df)} interactions into Neo4j using HIGH-SPEED UNWIND...")
    
    batch_size = 5000 # Tăng kích thước batch lên 5000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        # Nhóm dữ liệu theo loại hành động để chạy UNWIND hiệu quả
        grouped = batch.groupby('action')
        
        with neo4j_db.driver.session() as session:
            for action_name, group in grouped:
                rel_type = action_map.get(action_name.lower(), 'INTERACTED_WITH')
                
                # Chuẩn bị dữ liệu batch cho Cypher
                data_list = []
                for _, row in group.iterrows():
                    data_list.append({
                        'uid': int(row['user_id']),
                        'pid': int(row['product_id'])
                    })
                
                # Câu lệnh Cypher tối ưu: Nạp cả nghìn dòng trong 1 nốt nhạc
                query = f"""
                UNWIND $rows AS row
                MERGE (u:User {{id: row.uid}})
                MERGE (p:Product {{id: row.pid}})
                CREATE (u)-[:{rel_type} {{timestamp: timestamp(), weight: 1.0}}]->(p)
                """
                session.run(query, rows=data_list)
        
        print(f"Progress: {min(i + batch_size, len(df))}/{len(df)} lines seeded.")

    # Tính toán sự tương đồng giữa các User (User-User KB)
    print("Computing User-User similarities...")
    neo4j_db.compute_user_similarity()
    
    print("🏆 Graph KB seeded successfully!")

if __name__ == "__main__":
    seed_graph()
