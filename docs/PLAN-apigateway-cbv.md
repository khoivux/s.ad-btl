# 🧠 Project Plan: API Gateway Refactor (CBV)

## Context
The `api_gateway/app/views.py` file has grown to nearly 900 lines, encompassing proxy logic and rendering for all 7 microservices. This makes it difficult to maintain and prone to merge conflicts.

## Goal
Implement Option C from the brainstorm: Refactor the monolithic `views.py` into a modular `views/` Python package using Django Class-Based Views (CBVs) and a generic `BaseProxyView` to drastically reduce boilerplate code (DRY).

## Task Breakdown

### Phase 1: Core Foundation
- [ ] Create `api_gateway/app/views/` directory and `__init__.py`.
- [ ] Implement `base.py` containing:
  - `BaseProxyView`: Core logic for `proxy_request` (GET, POST, PUT, DELETE with automated error handling and logging).
  - `CustomerRequiredMixin`: Access control for customer-only endpoints.
  - `StaffRequiredMixin`: Access control for staff-only endpoints.

### Phase 2: Refactor by Domain
- [ ] **Books (`books.py`)**: `BookListView`, `BookSearchView`, `BookDetailView`, `BookReviewSubmitView`.
- [ ] **Auth & Customer (`customer.py`)**: `LoginView`, `RegisterView`, `LogoutView`, `ProfileView`, `AddressApiProxy`.
- [ ] **Cart (`cart.py`)**: `CartPageView`, `AddCartItemView`, `ModifyCartItemView`.
- [ ] **Orders & Checkout (`orders.py`)**: `CheckoutPageView`, `CheckoutApiView`, `OrderHistoryView`, `OrderDetailView`, `OrderTrackingView`, `OrderCancel/Delete Proxy`.
- [ ] **Loyalty & Vouchers (`vouchers.py`)**: `WalletDetailView`, `VoucherListView`, `VoucherShopView`.
- [ ] **Staff (`staff.py`)**: `StaffLoginView`, `StaffDashboardView`, `StaffBookManager`, `StaffVoucherManager`.

### Phase 3: Routing Integration
- [ ] Update `api_gateway/app/urls.py` to map to the new `Class.as_view()` endpoints.
- [ ] Resolve any import mapping issues.
- [ ] Safely delete the old `api_gateway/app/views.py`.

## Verification Checklist
- [ ] No `requests.exceptions.ConnectionError` causes a 500 unhandled crash (should be caught by BaseProxyView).
- [ ] Customer login and checkout flow operates normally.
- [ ] Staff login and book creation flow operates normally.

---
**Agent Assignments**:
- `backend-specialist`: To execute the Python Django refactoring and routing correctly.
