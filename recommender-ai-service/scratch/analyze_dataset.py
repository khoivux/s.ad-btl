import pandas as pd

df = pd.read_csv('c:/bookstore-micro05/recommender-ai-service/data_user500.csv')

stats = {
    'total_rows': len(df),
    'unique_users': df['user_id'].nunique(),
    'unique_products': df['product_id'].nunique(),
    'action_distribution': df['action'].value_counts().to_dict()
}

print("--- Data Statistics ---")
print(f"Total Rows: {stats['total_rows']}")
print(f"Unique Users: {stats['unique_users']}")
print(f"Unique Products: {stats['unique_products']}")
print("\nAction Distribution:")
for action, count in stats['action_distribution'].items():
    print(f" - {action}: {count}")
