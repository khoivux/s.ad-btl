# 📜 PROJECT RULES & ARCHITECTURE — MicroStore

Welcome to **MicroStore**, a high-performance, microservices-based e-commerce platform. This project has evolved from a simple bookstore into a multi-product ecosystem with advanced AI-driven recommendations.

---

## 🏗️ System Architecture

The project follows a **Microservices Architecture** with a central **API Gateway** acting as the entry point and SSR (Server-Side Rendering) engine.

### 1. Central API Gateway (`api_gateway`)
- **Role**: Routing, Authentication, Session Management, and SSR Frontend.
- **Technology**: Django (SSR with Tailwind CSS).
- **Pattern**: Uses `BaseProxyView` to forward requests to backend services.
- **Frontend**: Django Templates located in `app/templates/`.

### 2. Core Backend Services
- **`product-service`**: (New Core) Manages 11 product categories (Book, Laptop, Mobile, etc.) using PostgreSQL with JSONB for dynamic attributes.
- **`user-service`**: Unified service for Customers and Staff (Merged from legacy `staff-service` and `customer-service`). Uses MySQL.
- **`catalog-service`**: High-performance search and discovery using MongoDB. Syncs data from `product-service`.
- **`cart-service`**: In-memory/Postgres storage for user shopping carts.
- **`order-service`**: Handles checkout, order status, and inventory deduction.
- **`pay-service` & `ship-service`**: Handle payments and delivery logistics respectively.
- **`interaction-service`**: Logs user behaviors (view, add-to-cart, purchase) for AI training.
- **`recommender-ai-service`**: AI brain using LSTM/BiLSTM models and Neo4j Knowledge Graph to provide personalized picks.

### 3. Database Strategy (Polyglot Persistence)
- **PostgreSQL**: Transactional data (Product, Order, Pay, Ship, Cart, Comment).
- **MySQL**: Identity and Access Management (User).
- **MongoDB**: Search and Cataloging (Catalog, Interaction, AI cache).
- **Neo4j**: Relationship mapping for recommendations.

---

## 🚦 Development Rules & Conventions

### 1. The "Product" Pivot
> [!IMPORTANT]
> The project recently migrated from a "Book-only" model to a "General Product" model.
- **Rule**: Always use `product_id` instead of `book_id` in new code.
- **Legacy**: You will see some variables named `books` or `book_id` in templates/services. These are being phased out. Do not introduce new ones.

### 2. Inter-service Communication
- Services communicate primarily via **REST APIs**.
- In the Gateway, always extend `BaseProxyView` or `CustomerRequiredMixin` for proxying.
- Use internal container names (e.g., `http://product-service:8000`) for communication.

### 3. Product Schema
- All products are stored in a unified table.
- Dynamic specifications are stored in `attributes` (JSONB).
- When adding features for specific product types, use dynamic rendering (see `product_detail.html`).

### 4. Naming Conventions
- **APIs**: `/api/products/`, `/api/orders/`, etc.
- **Database Fields**: Snake case (`product_id`, `total_amount`).
- **Templates**: Descriptive names (`products.html`, `order_detail.html`).

---

## 📍 Current Project Status (Ongoing Work)

### ✅ Completed
- [x] Merge `staff` and `customer` services into `user-service`.
- [x] Create `product-service` with 11 categories support.
- [x] Migrate `order-service` and `cart-service` from `book_id` to `product_id`.
- [x] Refactor API Gateway to use Class-Based Views (CBVs).

### 🚧 In Progress (Unfinished)
- [ ] **Frontend Cleanup**: Some templates (`checkout.html`, `search.html`) still use `book.title` or `book.author`. These need to be generalized to `product.name` and dynamic attributes.
- [ ] **AI Model Integration**: The `recommender-ai-service` is currently being trained with LSTM/RNN models. Integration with the frontend "AI Pick" section is active but may need tuning.
- [ ] **Legacy File Removal**: Files like `books.html` or `book_detail.html` in `api_gateway` are deprecated and should be removed once full stability is confirmed.

---

## 🛠️ How to Work with This Project

1. **Spin up the stack**: `docker-compose up --build`.
2. **Logs**: Use `docker-compose logs -f <service-name>` for debugging.
3. **Migrations**: Run migrations inside containers: `docker exec -it <container> python manage.py migrate`.
4. **Documentation**: Refer to `docs/` for detailed migration plans and architecture diagrams.

---

## 🤖 Instructions for AI Agents
- **Prioritize the Migration Plan**: Before making changes to Order/Pay/Ship, read `docs/PLAN-order-pay-ship-migration.md`.
- **Be Aesthetic**: The frontend uses Tailwind CSS with a custom palette (indigo/amber). Keep designs premium and responsive.
- **Check Dependencies**: Changing a field in `product-service` often requires updates in `catalog-service` (sync) and `api_gateway` (view/template).

---
*Last Updated: 2026-05-13*
