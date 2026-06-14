import torch
import torch.nn as nn

class BaseRecommender(nn.Module):
    """Lớp cơ sở chứa các thành phần dùng chung như Embedding"""
    def __init__(self, num_products, num_actions, hidden_dim=256):
        super().__init__()
        self.prod_emb = nn.Embedding(num_products + 1, 64)
        self.act_emb = nn.Embedding(num_actions + 1, 16)
        self.input_dim = 64 + 16
        self.hidden_dim = hidden_dim

    def forward_embeddings(self, x):
        p_seq = x[:, :, 0]
        a_seq = x[:, :, 1]
        p_emb = self.prod_emb(p_seq)
        a_emb = self.act_emb(a_seq)
        return torch.cat([p_emb, a_emb], dim=-1)


class RNNRecommender(BaseRecommender):
    """Mô hình dựa trên Recurrent Neural Network cơ bản"""
    def __init__(self, num_products, num_actions, hidden_dim=128, num_layers=2):
        super().__init__(num_products, num_actions, hidden_dim)
        self.rnn = nn.RNN(self.input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2 if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim, num_products)

    def forward(self, x):
        rnn_in = self.forward_embeddings(x)
        out, _ = self.rnn(rnn_in)
        last_out = out[:, -1, :]
        return self.fc(last_out)


class LSTMRecommender(BaseRecommender):
    """Mô hình dựa trên Long Short-Term Memory (Tốt cho chuỗi dài)"""
    def __init__(self, num_products, num_actions, hidden_dim=128, num_layers=2):
        super().__init__(num_products, num_actions, hidden_dim)
        self.lstm = nn.LSTM(self.input_dim, hidden_dim, num_layers, batch_first=True, dropout=0.2 if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim, num_products)

    def forward(self, x):
        rnn_in = self.forward_embeddings(x)
        out, (hn, cn) = self.lstm(rnn_in)
        last_out = out[:, -1, :]
        return self.fc(last_out)


class BiLSTMRecommender(BaseRecommender):
    """Mô hình LSTM hai chiều (Hiểu ngữ cảnh cả trước và sau)"""
    def __init__(self, num_products, num_actions, hidden_dim=128, num_layers=2):
        super().__init__(num_products, num_actions, hidden_dim)
        self.lstm = nn.LSTM(self.input_dim, hidden_dim, num_layers, batch_first=True, bidirectional=True, dropout=0.2 if num_layers > 1 else 0)
        self.fc = nn.Linear(hidden_dim * 2, num_products) # *2 vì là bidirectional

    def forward(self, x):
        rnn_in = self.forward_embeddings(x)
        out, _ = self.lstm(rnn_in)
        last_out = out[:, -1, :]
        return self.fc(last_out)
