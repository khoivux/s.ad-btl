# Kế hoạch Huấn luyện Mô hình Recommendation (RNN, LSTM, BiLSTM)

Kế hoạch này chi tiết quy trình sử dụng bộ dữ liệu **RetailRocket** để huấn luyện 3 mô hình học sâu nhằm dự đoán hành vi người dùng (Next-Item Prediction) cho dự án MicroStore.

---

## 1. Phân tích Dữ liệu (RetailRocket)
Dựa trên cấu trúc file `events.csv`:
- **`timestamp`**: Thời gian tương tác.
- **`visitorid`**: ID người dùng (User).
- **`itemid`**: ID sản phẩm.
- **`event`**: Loại tương tác (`view`, `addtocart`, `transaction`).

---

## 2. Quy trình Tiền xử lý (Preprocessing)

### Bước 2.1: Làm sạch & Lọc dữ liệu
- Loại bỏ các `visitorid` chỉ có 1 tương tác (không đủ để tạo chuỗi).
- Mã hóa `itemid` thành các chỉ số (Indices) từ $0$ đến $V-1$ ($V$ là tổng số sản phẩm).
- Chuyển đổi `timestamp` để sắp xếp hành vi theo thời gian cho từng User.

### Bước 2.2: Tạo Chuỗi (Sequence Generation)
- Sử dụng phương pháp **Sliding Window**. Ví dụ: Cửa sổ kích thước $5$.
- **Input**: $[P_1, P_2, P_3, P_4, P_5]$ (5 sản phẩm đã xem).
- **Target**: $[P_6]$ (Sản phẩm tiếp theo).
- Áp dụng `Padding` cho các chuỗi ngắn hơn kích thước cửa sổ.

### Bước 2.3: Phân chia dữ liệu
- **Train (80%)**: Dùng để huấn luyện.
- **Validation (10%)**: Dùng để tinh chỉnh siêu tham số (Hyperparameters).
- **Test (10%)**: Đánh giá khách quan cuối cùng.

---

## 3. Kiến trúc Mô hình

Tất cả 3 mô hình sẽ có chung lớp đầu vào:
- **Embedding Layer**: Chuyển đổi `item_index` thành vector không gian (ví dụ: 128 dimensions).

### 3.1. Simple RNN
- **Cấu trúc**: `Embedding` -> `SimpleRNN (128 units)` -> `Dropout(0.2)` -> `Dense (Softmax)`.
- **Mục tiêu**: Thiết lập baseline đơn giản nhất cho mô hình chuỗi.

### 3.2. LSTM (Long Short-Term Memory)
- **Cấu trúc**: `Embedding` -> `LSTM (256 units)` -> `Dropout(0.3)` -> `Dense (Softmax)`.
- **Ưu điểm**: Khắc phục vấn đề triệt tiêu đạo hàm, ghi nhớ sở thích dài hạn tốt hơn RNN.

### 3.3. BiLSTM (Bidirectional LSTM)
- **Cấu trúc**: `Embedding` -> `Bidirectional(LSTM (128 units))` -> `GlobalMaxPool1D` -> `Dense (Softmax)`.
- **Ưu điểm**: Hiểu ngữ cảnh của chuỗi hành vi từ cả hai hướng (tuy nhiên trong thực tế realtime thường dùng LSTM, BiLSTM dùng để hiểu sâu dữ liệu offline).

---

## 4. Quy trình Huấn luyện & Đánh giá

### Thông số kỹ thuật
- **Loss Function**: `SparseCategoricalCrossentropy` (Vì target là Index).
- **Optimizer**: `Adam` (Learning rate: 0.001).
- **Batch Size**: 256 hoặc 512.

### Tiêu chí đánh giá (Metrics)
- **Recall@10**: Tỷ lệ sản phẩm thực tế nằm trong Top 10 gợi ý.
- **MRR@10 (Mean Reciprocal Rank)**: Đánh giá thứ hạng của sản phẩm đúng trong danh sách gợi ý.
- **Loss Curve**: Kiểm tra Overfitting qua đồ thị Loss của Train và Val.

---

## 5. Tích hợp vào Microservices

Sau khi huấn luyện, các model sẽ được đóng gói và sử dụng tại `recommender-ai-service`:
1. **Model Export**: Lưu model dưới dạng `.h5` hoặc `SavedModel`.
2. **Inference API**: 
   - Gateway nhận request từ người dùng.
   - Interaction Service gửi 10 hành động gần nhất của User.
   - Recommender Service đưa chuỗi này vào Model để lấy Top 10 gợi ý.
   - Kết quả được map ngược lại từ `Index` -> `Product ID` để hiển thị trên UI.

---

## 🚀 Các bước thực hiện tiếp theo (Next Steps)
1. Viết script `preprocess.py` để xử lý file CSV lớn của RetailRocket.
2. Xây dựng class `RecommendationModel` dùng chung cho cả 3 kiến trúc.
3. Tiến hành Training và vẽ đồ thị so sánh hiệu năng giữa RNN, LSTM và BiLSTM.

---
> [!NOTE]
> Do dữ liệu RetailRocket khá lớn (~900MB file events), việc huấn luyện nên được thực hiện trên GPU hoặc chia nhỏ dữ liệu (Sampling) nếu tài nguyên hạn chế.
