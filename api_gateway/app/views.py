from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json

BOOK_SERVICE_URL = "http://book-service:8000"
CUSTOMER_SERVICE_URL = "http://customer-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"
STAFF_SERVICE_URL = "http://staff-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"
COMMENT_RATE_SERVICE_URL = "http://comment-rate-service:8006"

def _log(label, r):
    """Helper to print response info to terminal."""
    print(f"[{label}] {r.request.method} {r.url} → {r.status_code}")
    try:
        print(f"        Response: {r.json()}")
    except Exception:
        print(f"        Response: {r.text[:200]}")

def book_list(request):
    search_query = request.GET.get('search', '')
    url = f"{BOOK_SERVICE_URL}/books/"
    if search_query:
        url += f"?search={search_query}"
    r = requests.get(url)
    _log("book_list", r)

    context = {"books": r.json(), "search": search_query}
    if 'customer_id' in request.session:
        context['customer_name'] = request.session.get('customer_name')
    return render(request, "books.html", context)

def search_view(request):
    """GET /search/ — Search, filter, and sort books."""
    q = request.GET.get('q', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort = request.GET.get('sort', '')

    url = f"{BOOK_SERVICE_URL}/books/?"
    params = []
    if q: params.append(f"q={q}")
    if min_price: params.append(f"min_price={min_price}")
    if max_price: params.append(f"max_price={max_price}")
    if sort: params.append(f"sort={sort}")
    
    if params:
        url += "&".join(params)

    try:
        r = requests.get(url)
        _log("search_view", r)
        books = r.json()
    except Exception as e:
        print(f"[search_view] Exception: {e}")
        books = []

    context = {
        "books": books,
        "q": q,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
    }
    if 'customer_id' in request.session:
        context['customer_name'] = request.session.get('customer_name')
        
    return render(request, "search.html", context)


def book_detail_view(request, book_id):
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/")
        _log(f"book_detail_view {book_id}", r)
        if r.status_code == 404:
            return render(request, "404.html", status=404)
        book = r.json()
    except Exception as e:
        print(f"[book_detail_view] Exception: {e}")
        return redirect('book_list')

    reviews_data = {'avg_rating': 0, 'total_reviews': 0, 'reviews': []}
    try:
        rr = requests.get(f"{COMMENT_RATE_SERVICE_URL}/reviews/{book_id}/")
        _log(f"book_detail_view reviews {book_id}", rr)
        if rr.status_code == 200:
            reviews_data = rr.json()
    except Exception as e:
        print(f"[book_detail_view] Reviews Exception: {e}")

    has_purchased = False
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            cr = requests.get(f"{ORDER_SERVICE_URL}/api/check-purchase/?customer_id={customer_id}&book_id={book_id}")
            _log(f"book_detail_view check_purchase", cr)
            if cr.status_code == 200:
                has_purchased = cr.json().get('has_purchased', False)
        except Exception as e:
            print(f"[book_detail_view] CheckPurchase Exception: {e}")

    context = {
        "book": book,
        "reviews_data": reviews_data,
        "has_purchased": has_purchased,
        "customer_id": customer_id,
        "customer_name": request.session.get('customer_name')
    }
    return render(request, "book_detail.html", context)


@csrf_exempt
def book_review_submit(request, book_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        data = json.loads(request.body)
        rating = data.get('rating')
        comment = data.get('comment', '')
        customer_name = request.session.get('customer_name', 'User')
        
        payload = {
            'customer_id': customer_id,
            'book_id': book_id,
            'rating': rating,
            'comment': comment,
            'customer_name': customer_name
        }
        
        r = requests.post(f"{COMMENT_RATE_SERVICE_URL}/reviews/", json=payload)
        _log(f"book_review_submit {book_id}", r)
        return JsonResponse(r.json(), status=r.status_code)
        
    except Exception as e:
        print(f"[book_review_submit] Exception: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def view_cart(request, customer_id):
    if 'customer_id' not in request.session:
        return redirect('login')
    if str(request.session['customer_id']) != str(customer_id):
        return redirect(f"/carts/{request.session['customer_id']}/")

    r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
    _log("view_cart", r)
    items = r.json()

    try:
        b = requests.get(f"{BOOK_SERVICE_URL}/books/")
        _log("view_cart [book_list]", b)
        books = b.json()
        book_map = {book['id']: book for book in books}
    except Exception:
        book_map = {}

    total_cart_price = 0
    for item in items:
        book_info = book_map.get(item['book_id'], {})
        item['title'] = book_info.get('title', 'Unknown Book')
        price = float(book_info.get('price', 0))
        item['price'] = f"{price:.2f}"
        item['subtotal'] = price * item['quantity']
        total_cart_price += item['subtotal']

    return render(request, "cart.html", {"items": items, "customer_name": request.session.get('customer_name'), "total_cart_price": total_cart_price})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            r = requests.post(f"{CUSTOMER_SERVICE_URL}/customers/login/", json={"email": email, "password": password})
            _log("login_view", r)
            if r.status_code == 200:
                user_data = r.json()
                request.session['customer_id'] = user_data['id']
                request.session['customer_name'] = user_data['name']
                return redirect('book_list')
            else:
                return render(request, "login.html", {"error": "Invalid email or password"})
        except Exception as e:
            print(f"[login_view] Exception: {e}")
            return render(request, "login.html", {"error": "Service Unavailable"})
    return render(request, "login.html")

def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password')
        try:
            r = requests.post(f"{CUSTOMER_SERVICE_URL}/customers/", json={"name": name, "email": email, "phone_number": phone_number, "password": password})
            _log("register_view", r)
            if r.status_code == 200 or r.status_code == 201:
                return redirect('login')
            else:
                return render(request, "register.html", {"error": r.json().get('error', 'Registration Failed')})
        except Exception as e:
            print(f"[register_view] Exception: {e}")
            return render(request, "register.html", {"error": "Service Unavailable"})
    return render(request, "register.html")

def logout_view(request):
    print(f"[logout_view] Customer {request.session.get('customer_id')} logged out")
    request.session.flush()
    return redirect('book_list')


@csrf_exempt
def add_cart_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payload = {
                "cart": data.get('cart_id') or request.session.get('customer_id', 1),
                "book_id": data.get('book_id'),
                "quantity": data.get('quantity', 1)
            }
            if 'customer_id' not in request.session:
                print("[add_cart_item] Unauthorized - no session")
                return JsonResponse({'error': 'Unauthorized', 'redirect': '/login'}, status=401)

            url = f"{CART_SERVICE_URL}/carts/items/"
            r = requests.post(url, json=payload)
            _log("add_cart_item", r)
            return JsonResponse(r.json(), status=r.status_code)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def modify_cart_item(request, item_id):
    url = f"{CART_SERVICE_URL}/carts/items/{item_id}/"

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            r = requests.put(url, json=data)
            _log(f"modify_cart_item [PUT] item={item_id}", r)
            return JsonResponse(r.json(), status=r.status_code)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        r = requests.delete(url)
        _log(f"modify_cart_item [DELETE] item={item_id}", r)
        if r.status_code == 204 or r.status_code == 200:
            return JsonResponse({'status': 'deleted'})
        return JsonResponse({'error': 'Failed to delete'}, status=r.status_code)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

# ─── Staff Views ──────────────────────────────────────────────────────────────

def staff_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            r = requests.post(f"{STAFF_SERVICE_URL}/staff/login/", json={"username": username, "password": password})
            _log("staff_login_view", r)
            if r.status_code == 200:
                data = r.json()
                request.session['staff_id'] = data['id']
                request.session['staff_name'] = data['username']
                return redirect('staff_dashboard')
            else:
                return render(request, "staff_login.html", {"error": "Invalid credentials"})
        except Exception as e:
            print(f"[staff_login_view] Exception: {e}")
            return render(request, "staff_login.html", {"error": f"Service Unavailable: {e}"})
    return render(request, "staff_login.html")


def staff_dashboard_view(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        _log("staff_dashboard_view [book_list]", r)
        books = r.json()
    except Exception as e:
        print(f"[staff_dashboard_view] Exception: {e}")
        books = []
    return render(request, "staff_dashboard.html", {
        "books": books,
        "staff_name": request.session.get('staff_name')
    })


def staff_logout_view(request):
    print(f"[staff_logout_view] Staff {request.session.get('staff_name')} logged out")
    request.session.pop('staff_id', None)
    request.session.pop('staff_name', None)
    return redirect('staff_login')


@csrf_exempt
def staff_add_book(request):
    if 'staff_id' not in request.session:
        return redirect('staff_login')
    if request.method == 'POST':
        payload = {
            "title": request.POST.get('title'),
            "author": request.POST.get('author'),
            "price": request.POST.get('price'),
            "stock": request.POST.get('stock', 0),
        }
        print(f"[staff_add_book] Payload: {payload}")
        try:
            r = requests.post(f"{STAFF_SERVICE_URL}/staff/books/", json=payload)
            _log("staff_add_book", r)
            if r.status_code in (200, 201):
                return redirect('staff_dashboard')
            return render(request, "staff_dashboard.html", {"error": r.json().get('error', 'Failed to add book')})
        except Exception as e:
            print(f"[staff_add_book] Exception: {e}")
            return render(request, "staff_dashboard.html", {"error": str(e)})
    return redirect('staff_dashboard')


@csrf_exempt
def staff_update_book(request, pk):
    if 'staff_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            print(f"[staff_update_book] book_id={pk} data={data}")
            r = requests.put(f"{STAFF_SERVICE_URL}/staff/books/{pk}/", json=data)
            _log(f"staff_update_book [PUT] book={pk}", r)
            return JsonResponse(r.json(), status=r.status_code)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def staff_delete_book(request, pk):
    if 'staff_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    if request.method == 'DELETE':
        print(f"[staff_delete_book] Deleting book_id={pk}")
        r = requests.delete(f"{STAFF_SERVICE_URL}/staff/books/{pk}/")
        _log(f"staff_delete_book [DELETE] book={pk}", r)
        if r.status_code in (200, 204):
            return JsonResponse({'status': 'deleted'})
        return JsonResponse({'error': 'Failed to delete'}, status=r.status_code)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

# ─── Checkout & Order Views ───────────────────────────────────────────────────

def checkout_page_view(request):
    """
    GET /checkout/ — Render the checkout confirmation page.
    Fetches cart items + book details (for order summary) and saved addresses.
    """
    if 'customer_id' not in request.session:
        return redirect('login')

    customer_id = request.session['customer_id']

    # Fetch cart items
    cart_items = []
    total = 0
    try:
        r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
        _log("checkout_page → cart", r)
        raw_items = r.json()
        for item in raw_items:
            book_r = requests.get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/")
            _log(f"checkout_page → book {item['book_id']}", book_r)
            book = book_r.json()
            subtotal = float(book['price']) * item['quantity']
            total += subtotal
            cart_items.append({
                'book_id': item['book_id'],
                'title': book.get('title', ''),
                'author': book.get('author', ''),
                'price': book['price'],
                'quantity': item['quantity'],
                'subtotal': round(subtotal, 2),
            })
    except Exception as e:
        print(f"[api-gateway][checkout_page] cart/book error: {e}")

    # Fetch saved addresses
    addresses = []
    try:
        addr_r = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/")
        _log("checkout_page → addresses", addr_r)
        if addr_r.status_code == 200:
            addresses = addr_r.json()
    except Exception as e:
        print(f"[api-gateway][checkout_page] address error: {e}")

    # Fetch customer details for auto-filling
    customer = {}
    try:
        cust_r = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/")
        _log("checkout_page → customer", cust_r)
        if cust_r.status_code == 200:
            customer = cust_r.json()
    except Exception as e:
        print(f"[api-gateway][checkout_page] customer err: {e}")

    # Fetch shipping methods
    shipping_methods = []
    try:
        ship_m_r = requests.get(f"{SHIP_SERVICE_URL}/api/shipping-methods/")
        _log("checkout_page → shipping_methods", ship_m_r)
        if ship_m_r.status_code == 200:
            shipping_methods = ship_m_r.json()
    except Exception as e:
        print(f"[api-gateway][checkout_page] shipping-methods err: {e}")

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "total": round(total, 2),
        "addresses": addresses,
        "shipping_methods": shipping_methods,
        "customer": customer,
        "customer_name": request.session.get('customer_name'),
        "customer_id": customer_id,
    })


@csrf_exempt
def checkout_view(request):
    """
    POST /checkout/ — Trigger the full checkout flow via order-service.
    Body: { customer_id, payment_method, shipping_address, contact_name, contact_phone }
    """
    if 'customer_id' not in request.session:
        return JsonResponse({'error': 'Unauthorized', 'redirect': '/login'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}

        customer_id = request.session['customer_id']
        # Compose full address string with contact info
        contact = f"{data.get('contact_name', '')} | {data.get('contact_phone', '')}"
        address_text = data.get('shipping_address', '')
        full_address = f"{contact}\n{address_text}"

        payload = {
            'customer_id': customer_id,
            'payment_method': data.get('payment_method', 'COD'),
            'shipping_address': full_address,
            'shipping_method': data.get('shipping_method', 'standard'),
            'shipping_fee': data.get('shipping_fee', 0),
        }
        print(f"[api-gateway][checkout] customer={customer_id} method={payload['payment_method']}")
        try:
            r = requests.post(f"{ORDER_SERVICE_URL}/orders/", json=payload)
            _log("checkout → order-service", r)
            if r.status_code in (200, 201):
                try:
                    requests.delete(f"{CART_SERVICE_URL}/carts/{customer_id}/clear/")
                except Exception as e:
                    print(f"[api-gateway][checkout] clear cart error: {e}")
            return JsonResponse(r.json(), status=r.status_code)
        except Exception as e:
            print(f"[api-gateway][checkout] Exception: {e}")
            return JsonResponse({'error': f'order-service unavailable: {e}'}, status=503)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def order_history_view(request):
    """GET /orders/ — Order history page for the logged-in customer."""
    if 'customer_id' not in request.session:
        return redirect('login')
    customer_id = request.session['customer_id']
    try:
        r = requests.get(f"{ORDER_SERVICE_URL}/orders/?customer_id={customer_id}")
        _log("order_history", r)
        orders = r.json()
    except Exception as e:
        print(f"[api-gateway][order_history] Exception: {e}")
        orders = []
    return render(request, "order_history.html", {
        "orders": orders,
        "customer_name": request.session.get('customer_name'),
    })


def order_detail_view(request, order_id):
    """GET /orders/<id>/ — Order confirmation / detail page."""
    try:
        r = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}/")
        _log(f"order_detail {order_id}", r)
        order = r.json()
    except Exception as e:
        print(f"[api-gateway][order_detail] Exception: {e}")
        order = {}

    # Fetch corresponding shipment
    shipment = {}
    try:
        if order.get('id'):
            s_r = requests.get(f"{SHIP_SERVICE_URL}/shipments/order/{order_id}/")
            _log(f"order_detail shipment {order_id}", s_r)
            if s_r.status_code == 200:
                shipment = s_r.json()
    except Exception as e:
        print(f"[api-gateway][order_detail] Shipment Exception: {e}")

    return render(request, "order_detail.html", {
        "order": order,
        "shipment": shipment,
        "customer_name": request.session.get('customer_name'),
    })


# ─── Address API Proxy ────────────────────────────────────────────────────────

@csrf_exempt
def address_list_create(request, customer_id):
    """GET/POST /api/addresses/<customer_id>/"""
    if request.method == 'GET':
        try:
            r = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/")
            _log(f"address_list {customer_id}", r)
            return JsonResponse(r.json(), safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=503)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
        try:
            r = requests.post(
                f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/",
                json=data
            )
            _log(f"address_create {customer_id}", r)
            return JsonResponse(r.json(), status=r.status_code)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=503)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def address_detail(request, customer_id, pk):
    """PUT/DELETE/PATCH /api/addresses/<customer_id>/<pk>/"""
    url = f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/{pk}/"
    try:
        if request.method == 'DELETE':
            r = requests.delete(url)
            _log(f"address_delete {pk}", r)
            return JsonResponse({'status': 'deleted'}, status=204)
        if request.method in ('PUT', 'PATCH'):
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = {}
            r = requests.patch(url, json=data) if request.method == 'PATCH' else requests.put(url, json=data)
            _log(f"address_update {pk}", r)
            return JsonResponse(r.json(), status=r.status_code)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=503)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
