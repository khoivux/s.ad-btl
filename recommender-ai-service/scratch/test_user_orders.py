import requests
import json

user_id = 3
print(f"--- Fetching wallet / points for user {user_id} ---")
try:
    r = requests.get(f"http://user-service:8000/users/{user_id}/")
    print(r.status_code, json.dumps(r.json(), indent=2))
except Exception as e:
    print("Error:", e)

print(f"\n--- Fetching orders from order-service for user {user_id} ---")
try:
    r = requests.get(f"http://order-service:8000/orders/?customer_id={user_id}")
    print(r.status_code, json.dumps(r.json(), indent=2))
except Exception as e:
    print("Error:", e)

print(f"\n--- Fetching direct interactions from Neo4j for user {user_id} ---")
try:
    from app.ai_core.neo4j_db import neo4j_db
    triples = neo4j_db.get_direct_interactions_context(user_id)
    print("Direct interactions context:", json.dumps(triples, indent=2))
    
    with neo4j_db.driver.session() as session:
        purch_res = session.run(
            "MATCH (u:User {id: $user_id})-[:PURCHASED]->(p:Product) RETURN p.title as title",
            user_id=int(user_id)
        )
        purchased_titles = list(set([r["title"] for r in purch_res]))
        print("Purchased titles from Neo4j:", purchased_titles)
except Exception as e:
    print("Error:", e)
