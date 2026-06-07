import os
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve, accuracy_score
import time

# Giả lập môi trường Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommender_ai_service.settings')
try:
    django.setup()
except:
    pass

from app.ai_core.models import RNNRecommender, LSTMRecommender, BiLSTMRecommender

from torch.utils.data import DataLoader, TensorDataset

from sklearn.metrics import f1_score

def prepare_data(csv_path, num_products=201, seq_len=10, sample_size=130212):
    print(f"Reading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    if len(df) > sample_size:
        print(f"Sampling {sample_size} interactions for training...")
        df = df.sample(sample_size, random_state=42)

    action_map = {
        'view': 1, 'click': 2, 'add_to_cart': 3, 'remove_from_cart': 4,
        'purchase': 5, 'wishlist': 6, 'rating': 7, 'comment': 7, 'search': 9
    }
    
    user_data = {}
    for _, row in df.iterrows():
        u, p, a = row['user_id'], row['product_id'], action_map.get(row['action'], 0)
        if u not in user_data: user_data[u] = []
        user_data[u].append((p, a))
        
    X, y = [], []
    for u, items in user_data.items():
        if len(items) < 2: continue
        for i in range(1, len(items)):
            seq = items[max(0, i-seq_len):i]
            target = (int(items[i][0]) - 1) % num_products
            num_seq = [[(int(p)-1)%num_products+1, a] for p, a in seq]
            while len(num_seq) < seq_len: num_seq.insert(0, [0, 0])
            X.append(num_seq)
            y.append(target)
            
    return train_test_split(np.array(X), np.array(y), test_size=0.1, random_state=42)

def top_k_accuracy(y_true, y_probs, k=10):
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    hits = [1 if y_true[i] in top_k_preds[i] else 0 for i in range(len(y_true))]
    return sum(hits) / len(y_true)

def train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products):
    print(f"\n--- Training {name} ---")
    model = model_class(num_products=num_products, num_actions=10)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.long), torch.tensor(y_train, dtype=torch.long))
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    
    X_test_t = torch.tensor(X_test, dtype=torch.long)
    losses = []
    start_time = time.time()
    
    epochs = 10
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for batch_X, batch_y in train_loader:
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
        probs = torch.softmax(logits, dim=1).numpy()
        preds = np.argmax(probs, axis=1)
        
    acc_top1 = accuracy_score(y_test, preds)
    acc_top10 = top_k_accuracy(y_test, probs, k=10)
    f1 = f1_score(y_test, preds, average='macro', zero_division=0)
    try: auc = roc_auc_score(y_test, probs, multi_class='ovr')
    except: auc = 0.5
        
    return {
        'name': name, 'top1': acc_top1, 'top10': acc_top10, 'f1': f1,
        'auc': auc, 'losses': losses, 'preds': preds, 'train_time': train_time
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
    plt.title('Accuracy Comparison: Top-1 vs Top-10')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('accuracy_comparison_bar.png')
    
    # 2. Loss Curves
    plt.figure(figsize=(10, 6))
    for r in results:
        plt.plot(r['losses'], label=f"{r['name']}")
    plt.title('Training Loss Convergence (20 Epochs)')
    plt.legend()
    plt.savefig('model_loss_curves.png')
    plt.close('all')

def main():
    csv_path = 'app/ai_core/behavior_dataset.csv'
    num_products = 201
    X_train, X_test, y_train, y_test = prepare_data(csv_path, num_products)
    
    results = []
    for model_class, name in [(RNNRecommender, "RNN"), (LSTMRecommender, "LSTM"), (BiLSTMRecommender, "BiLSTM")]:
        results.append(train_and_evaluate(model_class, name, X_train, X_test, y_train, y_test, num_products))
        
    plot_comparison(results)
    
    for res in results:
        plt.figure(figsize=(10, 8))
        cm = confusion_matrix(y_test, res['preds'])
        sns.heatmap(cm[:10, :10], annot=True, fmt='d', cmap='Blues')
        plt.title(f"Confusion Matrix (Top 10 Products) - {res['name']}")
        plt.savefig(f"confusion_matrix_{res['name']}.png")
        plt.close()

    best_res = max(results, key=lambda x: x['top10'])
    print(f"\n🏆 CHAMPION: {best_res['name']} with Top-10 Acc: {best_res['top10']*100:.2f}%")

if __name__ == "__main__":
    main()
