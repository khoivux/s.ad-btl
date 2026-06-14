# 🛒 MicroStore AI - Intelligent E-commerce Microservices

Chào mừng bạn đến với **MicroStore AI** - Hệ thống thương mại điện tử được xây dựng theo chuẩn kiến trúc **Microservices**, tích hợp sâu hệ thống Gợi ý (Recommender System) và Chatbot Tư vấn thông minh sử dụng kiến trúc lai **RAG (Retrieval-Augmented Generation) & LSTM (Deep Learning)**.

---

## 🌟 Kiến Trúc Hệ Thống (Architecture)

Dự án được phân tách thành các Domain riêng biệt nhằm tối ưu khả năng mở rộng (Scalability) và bảo trì (Maintainability), được kết nối qua API Gateway và Docker DNS:

| Dịch Vụ (Service) | Loại Database | Chức Năng Cốt Lõi |
| :--- | :--- | :--- |
| **API Gateway** (`:8000`) | N/A | Cổng giao tiếp chính, Load Balancing, Render giao diện (SSR) |
| **User Service** (`:8001`) | MySQL | Quản lý Tài khoản, Phân quyền, Tích điểm thành viên |
| **Product Service** (`:8002`) | PostgreSQL | Quản lý sản phẩm lõi, Tồn kho, Giá cả |
| **Cart Service** (`:8003`) | PostgreSQL | Quản lý Giỏ hàng của từng phiên làm việc |
| **Order Service** (`:8005`) | PostgreSQL | Quản lý Đơn đặt hàng, Trạng thái đơn, Lịch sử mua hàng |
| **Pay Service** (`:8006`) | PostgreSQL | Xử lý thanh toán, Giao dịch tài chính |
| **Ship Service** (`:8007`) | PostgreSQL | Vận chuyển, Theo dõi giao hàng (Tracking) |
| **Comment Rate Service** (`:8008`) | PostgreSQL | Quản lý Đánh giá, Bình luận, Chấm sao sản phẩm |
| **Catalog Service** (`:8009`) | MongoDB | Tìm kiếm & Hiển thị danh mục sản phẩm (NoSQL tốc độ cao) |
| **Recommender AI** (`:8010`) | Neo4j + ChromaDB | Bộ não AI: Chatbot RAG, Phân tích LSTM, Mạng lưới Đồ thị |
| **Interaction Service** (`:8011`)| MongoDB | Ghi nhận Hành vi người dùng (Click, View, Add to Cart) |

---

## 🧠 Lõi Công Nghệ AI (The AI Brain)
Điểm nhấn của dự án là **AI Consultant Chatbot** đặt tại service `recommender-ai-service`. Nó không phải là một Chatbot RAG thông thường mà là một mạng lưới đa tác vụ (Hybrid-RAG):

1. **Neural LSTM Ranking**: Dự đoán chuỗi hành vi mua sắm. Phân tích lịch sử click chuột của bạn để dự đoán món hàng tiếp theo bạn muốn mua.
2. **Knowledge Graph (Neo4j)**: Ánh xạ mạng lưới quan hệ `(User) -[ACTION]-> (Product)` giúp tính toán sự tương đồng (User Similarity) cực kỳ chuẩn xác và tốc độ cao.
3. **Vector Database (ChromaDB)**: Chứa các Embeddings của chính sách đổi trả, cẩm nang mua sắm và chi tiết sản phẩm.
4. **LLM Orchestrator (Google Gemini)**: Tổng hợp Context từ LSTM, Neo4j, DB truyền thống (Postgres) và Vector RAG vào cùng một Prompt để giao tiếp tự nhiên với khách hàng.

---

## 🚀 Khởi Động Nhanh (Quick Start)

### 1. Yêu Cầu Môi Trường
- **Docker** & **Docker Compose**
- **Python 3.10+** (nếu muốn debug local)

### 2. Khởi Chạy Hệ Thống
Chỉ cần chạy lệnh duy nhất để dựng toàn bộ 10+ containers (API + Databases):
```bash
docker-compose up -d --build
```

### 3. Nạp Dữ Liệu Mẫu (Database Seeding)
Để có dữ liệu giả lập trải nghiệm hệ thống (Mock Users, Products, Graph Nodes), chạy script:
```bash
# Trên Windows
.\db_seeders\run_all_seeds.bat
```

### 4. Huấn Luyện AI (Lần Đầu Tiên)
Sau khi nạp dữ liệu, bạn cần kích hoạt nơ-ron AI để Chatbot thông minh hơn.
*(Chi tiết các lệnh REST API nạp dữ liệu Vector và train LSTM, vui lòng xem tại tài liệu Setup)*.

---

## 📚 Tài Liệu Hướng Dẫn (Documentation)
Để hiểu sâu hơn về quy trình phát triển và các chuẩn mực của project, vui lòng đọc các tài liệu sau:

- 🎓 **[Báo Cáo Tiểu Luận (PDF)](./docs/tieuluanfinal.pdf)**: Báo cáo tổng kết đồ án trình bày chi tiết về kiến trúc hệ thống, thuật toán AI (LSTM, RAG) và kết quả nghiên cứu.
- 📖 **[SETUP_GUIDE.md](./SETUP_GUIDE.md)**: Hướng dẫn cài đặt, cấu hình biến môi trường (`GOOGLE_API_KEY`) và các lệnh Call API khởi tạo AI.
- 📜 **[RULES.md](./RULES.md)**: Các quy tắc lập trình nội bộ (Coding Conventions), Nhật ký thay đổi (Changelog) và tiến độ dọn dẹp hệ thống.
- 🏗️ **`docs/`**: Chứa sơ đồ luồng dữ liệu (Data Flow) và cấu trúc triển khai kỹ thuật bổ sung.

---
*14/06/2026*
