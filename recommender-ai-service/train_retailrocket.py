import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix
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

def prepare_retailrocket_data(csv_path, min_interactions=50, seq_len=10, sample_size=200000):
    print(f"Reading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # 1. Lọc sản phẩm phổ biến để giảm Vocabulary size
    counts = df['itemid'].value_counts()
    popular_items = counts[counts >= min_interactions].index
    df = df[df['itemid'].isin(popular_items)]
    
    print(f"Filtered to {len(popular_items)} popular items. Total interactions: {len(df)}")
    
    if len(df) > sample_size:
        print(f"Sampling {sample_size} interactions...")
        df = df.sample(sample_size, random_state=42)

    # 2. Map Item ID sang Index
    item_to_idx = {id: i + 1 for i, id in enumerate(popular_items)}
    num_products = len(popular_items)
    
    # 3. Map Event sang Action ID
    action_map = {
        'view': 1,
        'addtocart': 3,
        'transaction': 5
    }
    
    # 4. Gom nhóm theo người dùng và sắp xếp theo thời gian
    print("Grouping by visitor and sorting...")
    df = df.sort_values(['visitorid', 'timestamp'])
    user_data = {}
    for _, row in df.iterrows():
        u = row['visitorid']
        p = item_to_idx[row['itemid']]
        a = action_map.get(row['event'], 0)
        if u not in user_data: user_data[u] = []
        user_data[u].append((p, a))
        
    X, y = [], []
    print("Generating sequences...")
    for u, items in user_data.items():
        if len(items) < 2: continue
        for i in range(1, len(items)):
            seq = items[max(0, i-seq_len):i]
            target = items[i][0] - 1 # Target index (0 to num_products-1)
            
            # num_seq format: [[product_idx, action_id], ...]
            num_seq = [[p, a] for p, a in seq]
            while len(num_seq) < seq_len: num_seq.insert(0, [0, 0])
            X.append(num_seq)
            y.append(target)
            
    print(f"Total sequences generated: {len(X)}")
    
    # Lưu mapping để dùng cho inference sau này
    with open('retailrocket_item_map.pkl', 'wb') as f:
        pickle.dump(item_to_idx, f)
        
    return train_test_split(np.array(X), np.array(y), test_size=0.1, random_state=42), num_products

def top_k_accuracy(y_true, y_probs, k=10):
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    hits = [1 if y_true[i] in top_k_preds[i] else 0 for i in range(len(y_true))]
    return sum(hits) / len(y_true)

def train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products):
    print(f"\n--- Training {name} ---")
    model = model_class(num_products=num_products, num_actions=10)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.long), torch.tensor(y_train, dtype=torch.long))
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    X_test_t = torch.tensor(X_test, dtype=torch.long).to(device)
    losses = []
    start_time = time.time()
    
    epochs = 5 # Giảm epoch cho nhanh trong bản demo
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
    f1 = f1_score(y_test, preds, average='macro', zero_division=0)
    
    # AUC có thể rất chậm với 10k class, tạm thời bỏ qua hoặc dùng mẫu
    auc = 0.5 
        
    return {
        'name': name, 'top1': acc_top1, 'top10': acc_top10, 'f1': f1,
        'auc': auc, 'losses': losses, 'preds': preds, 'train_time': train_time,
        'model': model
    }

def plot_comparison(results):
    names = [r['name'] for r in results]
    top1 = [r['top1'] for r in results]
    top10 = [r['top10'] for r in results]
    
    # 1. Bar Chart: Top-1 vs Top-10 Accuracy
    x = np.arange(len(names))
    width = 0.35
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, top1, width, label='Top-1 Acc (Exact)')
    plt.bar(x + width/2, top10, width, label='Top-10 Acc (Hit Rate)')
    plt.xticks(x, names)
    plt.ylabel('Accuracy Score')
    plt.title('RetailRocket: Top-1 vs Top-10 Accuracy')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('retailrocket_accuracy_comparison.png')
    
    # 2. Loss Curves
    plt.figure(figsize=(10, 6))
    for r in results:
        plt.plot(r['losses'], label=f"{r['name']}")
    plt.title('RetailRocket: Training Loss Convergence')
    plt.legend()
    plt.savefig('retailrocket_loss_curves.png')
    plt.close('all')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'retailrocket-dataset', 'events.csv')
    # Tăng sample size để model học tốt hơn
    (X_train, X_test, y_train, y_test), num_products = prepare_retailrocket_data(csv_path, min_interactions=50, sample_size=300000)
    
    print(f"Vocabulary Size: {num_products} products.")
    
    results = []
    # Train cả 3 model
    for model_class, name in [(RNNRecommender, "RNN"), (LSTMRecommender, "LSTM"), (BiLSTMRecommender, "BiLSTM")]:
        results.append(train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products))
        
    plot_comparison(results)
    
    # BỔ SUNG: Vẽ Confusion Matrix cho từng model
    for res in results:
        plt.figure(figsize=(10, 8))
        cm = confusion_matrix(y_test, res['preds'])
        # Hiển thị 10 sản phẩm đầu tiên để khớp với logic của analyze_models.py
        sns.heatmap(cm[:10, :10], annot=True, fmt='d', cmap='Blues')
        plt.title(f"Confusion Matrix (Top 10) - {res['name']}")
        plt.savefig(f"retailrocket_cm_{res['name']}.png")
        plt.close()
        print(f"Saved confusion matrix for {res['name']}")
    
    # Lưu model tốt nhất (dựa trên top-10 acc)
    best_res = max(results, key=lambda x: x['top10'])
    print(f"\n🏆 CHAMPION: {best_res['name']} with Top-10 Acc: {best_res['top10']*100:.2f}%")
    
    torch.save(best_res['model'].state_dict(), 'retailrocket_best_model.pth')
    print(f"Best model saved to retailrocket_best_model.pth")

if __name__ == "__main__":
    main()
