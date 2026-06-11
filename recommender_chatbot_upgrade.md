# Kế hoạch nâng cấp Chatbot RAG cho 10 ngành hàng MicroStore

> [!NOTE]
> Kế hoạch này điều chỉnh chatbot AI từ chỗ chỉ hỗ trợ thông tin về sách sang hỗ trợ đầy đủ 10 ngành hàng của MicroStore, tích hợp tìm kiếm ngữ nghĩa (Semantic Search/Vector DB RAG) với bộ lọc độ tương đồng và chuẩn hóa các thuật ngữ của hệ thống.

---

## 📅 Các bước thực hiện

### Bước 1: Chuẩn bị tài liệu Kiến thức (KB Docs) mới
1. **Xóa file tri thức cũ**: `recommender-ai-service/app/kb_docs/advice.md` (chỉ chứa cẩm nang về sách).
2. **Cập nhật chính sách thành viên**: Sửa `recommender-ai-service/app/kb_docs/membership.md` đổi toàn bộ "MicroBook" -> "MicroStore".
3. **Cập nhật chính sách vận chuyển**: Sửa `recommender-ai-service/app/kb_docs/shipping.md` đổi toàn bộ "MicroBook" -> "MicroStore".
4. **Tạo mới 10 file tri thức** tương ứng 10 ngành hàng trong `recommender-ai-service/app/kb_docs/`:
   - `advice_book.md`: Hướng dẫn chọn sách, lộ trình học lập trình, sách thiếu nhi.
   - `advice_electronics.md`: Hướng dẫn chọn đồ công nghệ (thương hiệu, bảo hành).
   - `advice_fashion.md`: Cách chọn size quần áo, màu sắc phù hợp.
   - `advice_cosmetics.md`: Chọn mỹ phẩm theo loại da (skin_type), ngày hết hạn.
   - `advice_toys.md`: Chọn đồ chơi theo độ tuổi (age_group), chất liệu an toàn.
   - `advice_furniture.md`: Cách chọn nội thất theo chất liệu (gỗ, kim loại) và kích thước.
   - `advice_food.md`: Lưu ý hạn sử dụng và trọng lượng thực phẩm sạch.
   - `advice_medicine.md`: Lưu ý về hoạt chất (active ingredient) và liều lượng sử dụng.
   - `advice_pet_supplies.md`: Chọn thức ăn/phụ kiện theo loài thú cưng (animal_type).
   - `advice_auto_parts.md`: Hướng dẫn kiểm tra độ tương thích dòng xe cho phụ tùng.

---

### Bước 2: Tích hợp Semantic Search (Vector RAG) vào Chatbot
1. Cập nhật `recommender-ai-service/app/agents/rag_consultant.py`:
   - Import `vector_db` từ `..ai_core.vector_db`.
   - Trong hàm `get_advice_stream`:
     - Gọi `vector_db.query(user_message, n_results=3)` để lấy các đoạn tri thức khớp nhất.
     - Lọc kết quả (chỉ nhận các đoạn tài liệu có khoảng cách L2 `distance < 0.85` để lọc bỏ các câu hỏi xã giao hoặc không liên quan).
     - Nếu có tài liệu phù hợp, gộp chúng vào một mục `TÀI LIỆU HƯỚNG DẪN & CHÍNH SÁCH CỬA HÀNG` trong prompt.
     - Nếu không có tài liệu nào phù hợp (ví dụ hỏi xã giao), bỏ qua phần bối cảnh này để giữ prompt sạch sẽ.
   - Chuẩn hóa prompt: Đổi "HỒ SƠ ĐỘC GIẢ" thành "HỒ SƠ KHÁCH HÀNG" và loại bỏ hoàn toàn các từ ngữ mang xu hướng nhà sách cũ.

---

### Bước 3: Tạo Script Kích hoạt Re-index thủ công
Tạo file `recommender-ai-service/app/scripts/trigger_reindex.py` giúp kích hoạt nhanh tiến trình re-index toàn bộ ChromaDB thủ công qua API:
- Gửi yêu cầu `POST` tới endpoint `http://localhost:8000/api/recommender/index-kb/` (thông qua API Gateway) hoặc `http://recommender-ai-service:8000/index-kb/` trực tiếp.

---

## 🧪 Kịch bản kiểm thử (Verification Scenario)

1. **Khởi chạy lại hệ thống**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```
2. **Kích hoạt nạp dữ liệu (Index)**:
   Chạy script `trigger_reindex.py` để nạp toàn bộ 10 file tri thức mới và danh sách sản phẩm từ database vào ChromaDB.
3. **Kiểm thử chat thực tế**:
   - **Câu hỏi chính sách**: *"Silver được giảm bao nhiêu % và ship hỏa tốc bao nhiêu tiền?"* -> RAG phải tìm được `membership.md` và `shipping.md` và trả lời chính xác số liệu.
   - **Câu hỏi sản phẩm/Ngành hàng**: *"Mình muốn tìm mỹ phẩm cho da dầu"* -> RAG phải tìm được `advice_cosmetics.md` có ghi chú về skin_type da dầu và trả lời.
   - **Câu hỏi xã giao**: *"Bạn có khỏe không?"* -> RAG không kích hoạt (bỏ qua bối cảnh), AI trả lời xã giao bình thường.
