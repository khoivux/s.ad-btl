import torch
import torch.nn as nn
import requests
import os
import numpy as np
from django.conf import settings
from .neo4j_db import neo4j_db

from .models import LSTMRecommender, RNNRecommender, BiLSTMRecommender

PRODUCT_SERVICE_URL = "http://product-service:8000"

class BehaviorTrainer:
    def __init__(self, model_path="app/ai_core/behavior_model_best.pth", num_products=201):
        self.model_path = os.path.join(settings.BASE_DIR, model_path)
        self.action_map = {
            'view': 1, 'VIEW_PRODUCT': 1, 'VIEWED': 1,
            'click': 2, 'CLICK_PRODUCT': 2, 'CLICKED': 2,
            'add_to_cart': 3, 'ADD_TO_CART': 3, 'ADDED_TO_CART': 3,
            'remove_from_cart': 4, 'REMOVE_FROM_CART': 4,
            'purchase': 5, 'PURCHASE': 5, 'PURCHASED': 5,
            'wishlist': 6, 'WISHLIST_ADD': 6, 'WISHLISTED': 6,
            'review': 7, 'RATE_PRODUCT': 7, 'COMMENT_PRODUCT': 7, 'rating': 7, 'comment': 7, 'RATED': 7, 'COMMENTED': 7,
            'share': 8,
            'search': 9, 'SEARCHED': 9
        }
        self.num_products = num_products
        # Use LSTMRecommender as the default premium choice
        self.model = LSTMRecommender(num_products=num_products, num_actions=len(self.action_map))
        self.load()

    def load(self):
        if os.path.exists(self.model_path):
            try:
                # We need to knowing which model type was saved. 
                # For simplicity, if we suspect it might be LSTM after our recent talk, 
                # we'd need to adjust. But let's assume RNN for now as per previous run.
                # In a real system, we'd save metadata with the model.
                self.model.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu'), weights_only=True))
                print(f"[MODEL] Loaded best model from {self.model_path}")
            except Exception as e: 
                print(f"[MODEL] Failed to load model: {e}")

    def get_sequential_recommendations(self, user_id, top_k=10, cart_context=None):
        self.model.eval()
        seq_len = 10
        
        sim_boost = {}
        # 0. Integrated Real-time Cart Context into Social Boost (Graph)
        if cart_context:
            try:
                with neo4j_db.driver.session() as session:
                    # Look for items frequently bought with current items in cart
                    cart_sim_query = """
                    MATCH (pInCart:Product) WHERE pInCart.id IN $pids
                    MATCH (pInCart)<-[:INTERACTED_WITH]-(other:User)-[:INTERACTED_WITH]->(recProd:Product)
                    WHERE NOT recProd.id IN $pids
                    RETURN recProd.id as pid, count(other) as volume
                    ORDER BY volume DESC LIMIT 20
                    """
                    cart_recs = session.run(cart_sim_query, pids=[int(p) for p in cart_context])
                    for rec in cart_recs:
                        sim_boost[int(rec['pid'])] = sim_boost.get(int(rec['pid']), 0) + float(rec['volume']) * 2.0
            except Exception as e:
                print(f"[RECOM] Cart Neo4j context error: {e}")

        
        try:
            with neo4j_db.driver.session() as session:
                query = """
                MATCH (u:User {id: $uid})-[r]->(p:Product)
                RETURN p.id as pid, type(r) as action, r.timestamp as ts
                ORDER BY r.timestamp DESC LIMIT $limit
                """
                recs = session.run(query, uid=int(user_id), limit=seq_len)
                sequences = []
                for rec in recs:
                    p_id = (int(rec['pid']) - 1) % self.num_products
                    # Map Neo4j relationship types back to action strings if needed
                    # Our action_map in __init__ handles VIEWED, CLICKED etc. if we add them.
                    a_id = self.action_map.get(rec['action'], 0)
                    sequences.append([p_id, a_id])
                
                # Prepend cart context to sequence
                if cart_context:
                    context_seq = [[(int(pid)-1)%self.num_products, 2] for pid in cart_context]
                    sequences = (context_seq + sequences)[:seq_len]

                sequences = sequences[::-1]
                while len(sequences) < seq_len:
                    sequences.insert(0, [0, 0])
                
                seq_t = torch.tensor([sequences], dtype=torch.long)

        except Exception as e:
            print(f"[RECOM] Neo4j sequence fetch error: {e}")
            seq_t = torch.zeros((1, seq_len, 2), dtype=torch.long)

        with torch.no_grad():
            try:
                logits = self.model(seq_t)
                scores = torch.softmax(logits, dim=1).squeeze().tolist()
            except:
                scores = [0] * self.num_products

        # 2. Add Neighborhood Social Boost (Graph logic)
        try:

            with neo4j_db.driver.session() as session:
                sim_query = """
                MATCH (u:User {id: $uid})-[s:SIMILAR_TO]-(neighbor:User)-[]->(p:Product)
                RETURN p.id as pid, sum(s.weight) as score
                ORDER BY score DESC LIMIT 50
                """
                sim_recs = session.run(sim_query, uid=int(user_id))
                for rec in sim_recs:
                    pid = int(rec['pid'])
                    sim_boost[pid] = sim_boost.get(pid, 0) + float(rec['score'])

        except Exception:
            pass

        try:
            r = requests.get(f"{PRODUCT_SERVICE_URL}/products/?page_size=200", timeout=2)
            data = r.json()
            all_prods = data.get('results', []) if isinstance(data, dict) else data
        except Exception as e:
            print(f"[RECOM] Error fetching products in trainer: {e}")
            all_prods = []

        if cart_context:
            print(f"[RECOM] Cart Context items: {cart_context} | SimBoost entries: {len(sim_boost)}")

        results = []
        for p in all_prods:

            try:
                pid = int(p['id'])
                idx = (pid - 1) % self.num_products
                n_score = scores[idx] if idx < len(scores) else 0
                # Higher divisor for social boost to keep percentage reasonable
                s_boost = sim_boost.get(pid, 0) * 0.01 
                
                # Hybrid score capped at 0.99 for UI friendliness
                final_score = min(0.99, (n_score * 0.8) + (s_boost * 0.2))

                
                results.append({
                    'id': pid,
                    'title': p.get('name') or p.get('title'),
                    'price': p.get('price'),
                    'image_url': p.get('image_url'),
                    'score': float(final_score),
                    'final_score': float(final_score),
                    'social_proof': f"Gợi ý từ cộng đồng" if pid in sim_boost else "",
                    'description': p.get('description', ''),
                    'product_type': p.get('product_type', 'General'),
                    'domain_data': p.get('domain_data', {})
                })
            except Exception as e:
                print(f"[DEBUG-TRAINER] Error processing prod: {e}")

        print(f"[DEBUG-TRAINER] Generated {len(results)} ranked products.")
        results.sort(key=lambda x: x['final_score'], reverse=True)
        return results[:top_k]

    def save(self):
        torch.save(self.model.state_dict(), self.model_path)
        print(f"[TRAINER] Model saved to {self.model_path}")

    def train_epoch(self, interactions, epochs=10):
        """
        Huấn luyện mô hình chuỗi với hiệu năng cao (Mini-batching).
        """
        from torch.utils.data import DataLoader, TensorDataset
        
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        
        # 1. Chuẩn bị dữ liệu (Gộp theo user)
        user_data = {}
        for row in interactions:
            u, p, a = row['user_id'], row['product_id'], row['action']
            if u not in user_data: user_data[u] = []
            user_data[u].append((p, a))
            
        X, y = [], []
        seq_len = 10
        for u, items in user_data.items():
            if len(items) < 2: continue
            for i in range(1, len(items)):
                seq = items[max(0, i-seq_len):i]
                target = (int(items[i][0]) - 1) % self.num_products
                
                num_seq = []
                for p, a in seq:
                    p_id = (int(p) - 1) % self.num_products + 1
                    a_id = self.action_map.get(a, 0)
                    num_seq.append([p_id, a_id])
                
                while len(num_seq) < seq_len:
                    num_seq.insert(0, [0, 0])
                X.append(num_seq)
                y.append(target)

        if not X:
            print("[TRAINER] Không có đủ dữ liệu chuỗi để huấn luyện.")
            return False

        # 2. Sử dụng DataLoader để tối ưu tốc độ và bộ nhớ
        X_t = torch.tensor(X, dtype=torch.long)
        y_t = torch.tensor(y, dtype=torch.long)
        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=128, shuffle=True)
        
        print(f"[TRAINER] Bắt đầu huấn luyện trên {len(X)} chuỗi hành vi...")
        
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(loader)
            print(f"[TRAINER] Epoch [{epoch+1}/{epochs}], Loss trung bình: {avg_loss:.4f}")
        
        return True

# Singleton instance
behavior_trainer = BehaviorTrainer()
