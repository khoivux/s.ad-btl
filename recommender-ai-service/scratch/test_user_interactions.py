import requests

INTERACTION_SERVICE_URL = "http://localhost:8011"
user_id = 3

print(f"Fetching interaction logs for user ID {user_id} (customer@example.com)...")
try:
    r_logs = requests.get(f"{INTERACTION_SERVICE_URL}/logs/user/{user_id}/", timeout=5)
    if r_logs.status_code == 200:
        logs = r_logs.json()
        print(f"\nTotal interactions found: {len(logs)}")
        for log in logs[:30]:
            print(f"- Action: {log.get('action')}, Product ID: {log.get('product_id')}, Timestamp: {log.get('timestamp')}")
    else:
        print(f"Failed to fetch logs: {r_logs.status_code} - {r_logs.text}")
except Exception as e:
    print(f"Error occurred: {e}")
