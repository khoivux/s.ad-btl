# Order & Delivery Flow Implementation (Option B)

## Overview
Implement an automated order dispatch and delivery flow (Option B) where payment status drives order progression, and shippers can actively accept and complete deliveries. This provides a modern, semi-automated e-commerce experience.

## Project Type
BACKEND & WEB (Microservices architecture)

## Success Criteria
- Orders paid online automatically move to `processing`.
- COD orders move to `pending_confirmation` and require Staff approval to reach `processing`.
- Staff can mark an order as `ready_for_pickup`.
- System dispatches the order to `ship-service`.
- Shipper can accept an order (moves to `delivering`).
- Shipper can complete an order (moves to `completed`), which triggers a loyalty point update.

## Tech Stack
- **Languages/Frameworks**: Python, Django, Django REST Framework
- **Architecture**: Microservices (order-service, pay-service, ship-service, staff-service)
- **Communication**: Synchronous HTTP Requests (for simplicity in current architecture) or async events if broker exists.

## File Structure
- `order-service/app/models.py` (Update Order status choices)
- `order-service/app/views.py` (Add dispatch & completion webhooks)
- `ship-service/app/models.py` (Create Delivery model)
- `ship-service/app/views.py` (Shipper accept/complete endpoints)
- `api_gateway/app/views/orders.py` & `staff.py` & `shipper.py` (Route coordination)
- `api_gateway/app/templates/*` (UI updates for Staff and Shipper)

## Task Breakdown

### Task 1: Order Status & Data Model Updates
- **Agent**: `backend-specialist`
- **Dependencies**: None
- **INPUT**: Current `Order` model in `order-service`.
- **OUTPUT**: Updated `status` choices (`pending`, `pending_confirmation`, `processing`, `ready_for_pickup`, `delivering`, `completed`, `cancelled`).
- **VERIFY**: Run migrations successfully.

### Task 2: Payment Integration Logic (Auto-Processing)
- **Agent**: `backend-specialist`
- **Dependencies**: Task 1
- **INPUT**: Checkout and Payment Webhook views.
- **OUTPUT**: Logic to set online payments to `processing` and COD to `pending_confirmation`.
- **VERIFY**: Unit test or manual test checkout flows for both payment methods.

### Task 3: Staff Order Management
- **Agent**: `backend-specialist`, `frontend-specialist`
- **Dependencies**: Task 2
- **INPUT**: Staff dashboard orders view.
- **OUTPUT**: Buttons for Staff to "Approve COD Order" (→ `processing`) and "Mark Ready for Pickup" (→ `ready_for_pickup` & dispatch to ship-service).
- **VERIFY**: Staff can click buttons and status updates in DB.

### Task 4: Ship Service Delivery Management
- **Agent**: `backend-specialist`
- **Dependencies**: Task 3
- **INPUT**: `ship-service` API.
- **OUTPUT**: Endpoint to receive dispatched order. Endpoints for Shipper to "Accept Order" (→ `delivering`) and "Complete Delivery" (→ `completed` in both ship and order services).
- **VERIFY**: API endpoints test successfully via Postman/cURL.

### Task 5: Loyalty Points Integration
- **Agent**: `backend-specialist`
- **Dependencies**: Task 4
- **INPUT**: Customer model / Loyalty endpoint.
- **OUTPUT**: When order is `completed`, trigger an API call to customer-service to add loyalty points.
- **VERIFY**: Check customer record after order completion.

### Task 6: Shipper UI
- **Agent**: `frontend-specialist`
- **Dependencies**: Task 4
- **INPUT**: Shipper dashboard HTML/JS.
- **OUTPUT**: UI showing available orders, button to accept, and button to complete.
- **VERIFY**: Shipper can visually process a complete order lifecycle.

## Phase X: Verification
- [ ] Lint: Run `flake8` or equivalent on modified Python files.
- [ ] Security: Ensure only authorized roles (Staff/Shipper) can hit status-change endpoints.
- [ ] E2E Test: Place COD order -> Staff Approve -> Staff Ready -> Shipper Accept -> Shipper Complete -> Verify Loyalty Points.
- [ ] Build/Deploy: docker compose up runs without errors.
