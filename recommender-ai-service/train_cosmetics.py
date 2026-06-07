import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from torch.utils.data import DataLoader, TensorDataset
import time
import pickle

# Giả lập môi trường Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender_ai_service.settings')
try:
    django.setup()
except:
    pass

from app.ai_core.models import RNNRecommender, LSTMRecommender, BiLSTMRecommender

def prepare_cosmetics_data(csv_path, min_interactions=50, seq_len=10, sample_size=200000):
    print(f"Reading dataset from {csv_path}...")
    # Dataset này có event_time là string, cần convert
    df = pd.read_csv(csv_path)
    
    # 1. Lọc sản phẩm phổ biến
    counts = df['product_id'].value_counts()
    popular_items = counts[counts >= min_interactions].index
    df = df[df['product_id'].isin(popular_items)]
    
    print(f"Filtered to {len(popular_items)} popular items. Total interactions: {len(df)}")
    
    if len(df) > sample_size:
        print(f"Sampling {sample_size} interactions...")
        df = df.sample(sample_size, random_state=42)

    # 2. Map Product ID sang Index
    item_to_idx = {id: i + 1 for i, id in enumerate(popular_items)}
    num_products = len(popular_items)
    
    # 3. Map Event Type sang Action ID
    action_map = {
        'view': 1,
        'cart': 3,
        'remove_from_cart': 4,
        'purchase': 5
    }
    
    # 4. Gom nhóm theo người dùng/session và sắp xếp theo thời gian
    print("Converting event_time and sorting...")
    df['event_time'] = pd.to_datetime(df['event_time'])
    df = df.sort_values(['user_id', 'event_time'])
    
    user_data = {}
    for _, row in df.iterrows():
        u = row['user_id']
        p = item_to_idx[row['product_id']]
        a = action_map.get(row['event_type'], 0)
        if u not in user_data: user_data[u] = []
        user_data[u].append((p, a))
        
    X, y = [], []
    print("Generating sequences...")
    for u, items in user_data.items():
        if len(items) < 2: continue
        for i in range(1, len(items)):
            seq = items[max(0, i-seq_len):i]
            target = items[i][0] - 1
            
            num_seq = [[p, a] for p, a in seq]
            while len(num_seq) < seq_len: num_seq.insert(0, [0, 0])
            X.append(num_seq)
            y.append(target)
            
    print(f"Total sequences generated: {len(X)}")
    
    with open('cosmetics_item_map.pkl', 'wb') as f:
        pickle.dump(item_to_idx, f)
        
    return train_test_split(np.array(X), np.array(y), test_size=0.1, random_state=42), num_products

def top_k_accuracy(y_true, y_probs, k=10):
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    hits = [1 if y_true[i] in top_k_preds[i] else 0 for i in range(len(y_true))]
    return sum(hits) / len(y_true)

def train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products):
    print(f"\n--- Training {name} (Cosmetics) ---")
    model = model_class(num_products=num_products, num_actions=10)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.long), torch.tensor(y_train, dtype=torch.long))
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    X_test_t = torch.tensor(X_test, dtype=torch.long).to(device)
    losses = []
    start_time = time.time()
    
    epochs = 5
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        avg_loss = epoch_loss / len(train_loader)
        losses.append(avg_loss)
        print(f"  Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
            
    train_time = time.time() - start_time
    model.eval()
    with torch.no_grad():
        logits = model(X_test_t)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
        preds = np.argmax(probs, axis=1)
        
    acc_top1 = accuracy_score(y_test, preds)
    acc_top10 = top_k_accuracy(y_test, probs, k=10)
    
    return {
        'name': name, 'top1': acc_top1, 'top10': acc_top10, 
        'losses': losses, 'preds': preds, 'train_time': train_time,
        'model': model
    }

def main():
    csv_path = 'dataset2/2020-Jan.csv'
    (X_train, X_test, y_train, y_test), num_products = prepare_cosmetics_data(csv_path, min_interactions=50, sample_size=200000)
    
    results = []
    for model_class, name in [(RNNRecommender, "RNN"), (LSTMRecommender, "LSTM"), (BiLSTMRecommender, "BiLSTM")]:
        results.append(train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products))
    
    # Vẽ Accuracy Comparison
    names = [r['name'] for r in results]
    top10 = [r['top10'] for r in results]
    plt.figure(figsize=(10, 6))
    plt.bar(names, top10, color='pink')
    plt.title('Cosmetics Shop: Top-10 Accuracy Comparison')
    plt.ylabel('Accuracy')
    plt.savefig('cosmetics_accuracy_comparison.png')
    
    # Vẽ Confusion Matrix cho Champion
    best_res = max(results, key=lambda x: x['top10'])
    plt.figure(figsize=(10, 8))
    cm = confusion_matrix(y_test, best_res['preds'])
    sns.heatmap(cm[:10, :10], annot=True, fmt='d', cmap='PuRd')
    plt.title(f"Cosmetics Confusion Matrix (Top 10) - {best_res['name']}")
    plt.savefig(f"cosmetics_cm_{best_res['name']}.png")
    
    print(f"\n🏆 CHAMPION (Cosmetics): {best_res['name']} with Top-10 Acc: {best_res['top10']*100:.2f}%")
    torch.save(best_res['model'].state_dict(), 'cosmetics_best_model.pth')

if __name__ == "__main__":
    main()
