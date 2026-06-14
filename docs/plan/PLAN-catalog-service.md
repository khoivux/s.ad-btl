# PLAN: Catalog Service Implementation

## 1. Goal (Mục tiêu)
Xây dựng `catalog-service` sử dụng **MongoDB** làm cơ sở dữ liệu để lưu trữ bản sao read-optimized (tối ưu tốc độ đọc) của toàn bộ Dữ liệu Sách (Tác giả, Tiêu đề, Thể loại, Giá bán...).
Mục đích: Tách biệt luồng Đọc/Tìm kiếm (Discovery) ra khỏi luồng Ghi/Quản lý gốc của `book-service` (mô hình CQRS Pattern).

## 2. Giải đáp: Tại sao "Tìm kiếm sách" lại giao cho Catalog Service?
Trong kiến trúc Microservices E-commerce, từ **"Catalog"** không mang nghĩa hạn hẹp là "Thể loại/Danh mục" (Category), mà nó ám chỉ **"Danh mục/vựng tập Sản phẩm"** (Product Catalog). 
- `book-service`: Nắm giữ bản ghi gốc (Source of Truth) - dùng để cho Staff/Admin thêm sửa xóa dữ liệu, thay đổi trạng thái kho (Mất nhiều thời gian xử lý Transaction và Validate).
- `catalog-service`: Nhận dữ liệu đồng bộ (Sync) từ `book-service`, gộp lại thành một cục Data gọn nhẹ thả vào MongoDB. MongoDB lưu dữ liệu kiểu JSON Document, cung cấp giải pháp Index (Chỉ mục) cực kỳ nhanh. Lọc giá (nhỏ hơn, lớn hơn), Lọc Full-text Search Theo Tiêu đề (Title), Lọc Category đều siêu tốc độ mà không "băm" nát database chính.

Do đó, toàn bộ nghiệp vụ **TÌM KIẾM, KHÁM PHÁ** (Search/Filter/List) đều được quy tụ về `catalog-service`. Trang chủ Frontend (hoặc API Gateway) sẽ chọc thẳng vào Service này để lấy danh sách và tìm kiếm dựa trên Tiêu Đề, Giá, v.v..

## 3. Kiến trúc (Architecture Decisions)
- **Database**: MongoDB (dễ dàng tìm kiếm text và xử lý các field linh hoạt).
- **Data Sync**: Bắn API (Synchronous HTTP Call). Khi sách được Create/Update/Delete bên `book-service`, `book-service` tự động gọi POST/PUT sang nội bộ của `catalog-service` để ra lệnh nó Update lại Document ở MongoDB.
- **Routing**: API Gateway `GET /books/` (Trang chủ) và `GET /search/` sẽ được trỏ sang `catalog-service`.

## 4. Task Breakdown (Kế hoạch hành động)
- [ ] **Task 1: Khởi tạo Service**
  - Setup thư mục `catalog-service` dùng framework Django/DRF (hoặc FastAPI để hợp PyMongo).
  - Cấu hình `docker-compose.yml` để nhúng image `mongo` và build `catalog-service`.
- [ ] **Task 2: API Phục vụ Tìm kiếm (Catalog Service)**
  - `GET /catalog/books/`: Lọc sách (Price min/max, Category, Ordering).
  - `GET /catalog/books/<id>/`: Chi tiết sách (về mặt nội dung tĩnh).
  - `GET /catalog/search?q=...`: Tìm kiếm bằng chỉ mục Full-Text MongoDB.
  - `POST/PUT/DELETE /catalog/sync/`: Các API nội bộ nhận lệnh Update từ Book Service.
- [ ] **Task 3: Cập nhật Book Service (Publisher)**
  - Sửa `book-service/app/views.py` (Chỗ mà StaffBookApiView thêm sửa xóa sách).
  - Viết 1 Trigger con: Sau khi lưu `.save()` thành công, dùng `requests.post()` tới `catalog-service` để đồng bộ bản ghi đó qua Mongo.
- [ ] **Task 4: Chuyển hướng API Gateway**
  - Sửa `api_gateway/app/views/books.py` trỏ các `proxy_request` lấy list sách và search sang `catalog-service`.

## 5. Agents Phụ Trách
- `@backend-specialist`: Xây dựng kết nối MongoDB và API CRUD, Code logic Data Sync.
- `@orchestrator`: Cấu hình Docker Compose và điều hướng luồng API Gateway.
