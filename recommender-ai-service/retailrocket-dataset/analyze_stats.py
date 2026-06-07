import pandas as pd

df = pd.read_csv('c:/bookstore-micro05/recommender-ai-service/retailrocket-dataset/events.csv')
num_items = df['itemid'].nunique()
num_users = df['visitorid'].nunique()
num_events = len(df)

print(f"Items: {num_items}")
print(f"Users: {num_users}")
print(f"Events: {num_events}")
print(f"Events per item: {num_events / num_items:.2f}")
print(f"Events per user: {num_events / num_users:.2f}")
