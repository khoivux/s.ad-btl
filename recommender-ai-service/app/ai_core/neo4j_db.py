import os
from django.conf import settings
from neo4j import GraphDatabase

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'none')

class Neo4jDBManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jDBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self._initialized = True
        self.create_constraints()

    def create_constraints(self):
        """Tạo Index để tăng tốc truy vấn lên 100 lần"""
        queries = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE INDEX product_title_index IF NOT EXISTS FOR (p:Product) ON (p.title)"
        ]
        with self.driver.session() as session:
            for q in queries:
                try: session.run(q)
                except: pass

    def close(self):
        self.driver.close()

    def merge_user(self, user_id):
        query = """
        MERGE (u:User {id: $user_id})
        RETURN u
        """
        with self.driver.session() as session:
            session.run(query, user_id=user_id)

    def merge_product(self, product_id, title, category):
        query = """
        MERGE (p:Product {id: $product_id})
        SET p.title = $title
        MERGE (c:Category {name: $category})
        MERGE (p)-[:BELONGS_TO]->(c)
        RETURN p
        """
        with self.driver.session() as session:
            session.run(query, product_id=product_id, title=title, category=category)

    def record_interaction(self, user_id, product_id, action, weight=1.0):
        """
        Records an interaction between User and Product with specific relationship types.
        """
        # Map action to relationship type
        action_map = {
            'view': 'VIEWED',
            'click': 'CLICKED',
            'wishlist': 'WISHLISTED',
            'add_to_cart': 'ADDED_TO_CART',
            'purchase': 'PURCHASED',
            'search': 'SEARCHED',
            'rating': 'RATED',
            'comment': 'COMMENTED'
        }
        rel_type = action_map.get(action.lower(), action.upper())

        query = f"""
        MERGE (u:User {{id: $user_id}})
        MERGE (p:Product {{id: $product_id}})
        CREATE (u)-[r:{rel_type}]->(p)
        SET r.weight = $weight, r.timestamp = timestamp()
        RETURN r
        """
        with self.driver.session() as session:
            session.run(query, user_id=user_id, product_id=product_id, weight=weight)

    def get_user_interactions(self, user_id, limit=20):
        """
        Gets sequential interactions of a user to construct input for LSTM
        """
        query = """
        MATCH (u:User {id: $user_id})-[r]->(p:Product)
        RETURN type(r) as action, p.id as product_id, r.timestamp as timestamp
        ORDER BY r.timestamp DESC
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id, limit=limit)
            return [{"action": record["action"], "product_id": record["product_id"], "timestamp": record["timestamp"]} for record in result]

    def get_recommendation_context(self, user_id):
        """
        GraphRAG Retrieval: Finds items viewed/bought by similar users.
        """
        query = """
        MATCH (u:User {id: $user_id})-[:VIEWED|CLICKED|ADDED_TO_CART|PURCHASED]->(p:Product)<-[:VIEWED|CLICKED|ADDED_TO_CART|PURCHASED]-(other:User)-[:PURCHASED|ADDED_TO_CART]->(rec:Product)
        WHERE NOT (u)-[:VIEWED|CLICKED|ADDED_TO_CART|PURCHASED]->(rec)
        RETURN rec.id as product_id, rec.title as title, count(*) as freq
        ORDER BY freq DESC
        LIMIT 10
        """
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id)
            return [{"product_id": record["product_id"], "title": record["title"], "freq": record["freq"]} for record in result]
            
    def get_direct_interactions_context(self, user_id):
        """
        Gets the recent things this user interacted with for prompt context
        """
        query = """
        MATCH (u:User {id: $user_id})-[r]->(p:Product)
        RETURN type(r) as action, p.title as title, p.id as product_id
        ORDER BY r.timestamp DESC
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, user_id=user_id)
            return [{"action": record["action"], "title": record["title"], "product_id": record["product_id"]} for record in result]

    def compute_user_similarity(self):
        """
        Phiên bản BATCHING: Chia nhỏ việc tính toán tương đồng để bảo vệ RAM.
        Tính toán dựa trên PURCHASED, ADDED_TO_CART, WISHLISTED.
        """
        # 1. Lấy danh sách tất cả User ID
        with self.driver.session() as session:
            result = session.run("MATCH (u:User) RETURN u.id as id")
            user_ids = [record["id"] for record in result]

        print(f"[NEO4J] Bắt đầu tính tương đồng cho {len(user_ids)} người dùng (Batching mode)...")
        
        # 2. Chia mẻ (Batch size: 500 users)
        batch_size = 500
        for i in range(0, len(user_ids), batch_size):
            current_batch = user_ids[i:i+batch_size]
            
            query = """
            MATCH (u1:User)-[:PURCHASED|ADDED_TO_CART|WISHLISTED]->(p:Product)<-[:PURCHASED|ADDED_TO_CART|WISHLISTED]-(u2:User)
            WHERE u1.id IN $batch_ids AND u1.id < u2.id
            WITH u1, u2, count(p) as common_prods
            WHERE common_prods >= 2
            MERGE (u1)-[s:SIMILAR_TO]-(u2)
            SET s.weight = common_prods
            """
            
            with self.driver.session() as session:
                session.run(query, batch_ids=current_batch)
            
            print(f"  - Đã xử lý tương đồng cho cụm người dùng {i+1} đến {min(i+batch_size, len(user_ids))}")

# Singleton access
neo4j_db = Neo4jDBManager()
