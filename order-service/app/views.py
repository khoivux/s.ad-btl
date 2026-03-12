from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem
from .serializers import OrderSerializer
import requests
import decimal

CART_SERVICE_URL = "http://cart-service:8000"
BOOK_SERVICE_URL = "http://book-service:8000"
PAY_SERVICE_URL  = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"

def _log(tag, r):
    print(f"[order-service][{tag}] {r.request.method} {r.url} → {r.status_code}")

class OrderListCreate(APIView):
    """
    POST /orders/  → Checkout: Create order, process payment, create shipment.
    GET  /orders/?customer_id=<id> → Order history for a customer.
    """
    def post(self, request):
        customer_id = request.data.get('customer_id')
        payment_method = request.data.get('payment_method', 'COD')
        shipping_address = request.data.get('shipping_address', '')
        shipping_method = request.data.get('shipping_method', 'standard')
        shipping_fee = decimal.Decimal(str(request.data.get('shipping_fee', 0)))

        if not customer_id:
            return Response({'error': 'customer_id is required'}, status=400)

        # ── Step 1: Fetch cart items ───────────────────────────────────────────
        print(f"[order-service] Step 1: Fetching cart for customer {customer_id}")
        try:
            cart_resp = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
            _log("fetch_cart", cart_resp)
            cart_items = cart_resp.json()
        except Exception as e:
            return Response({'error': f'cart-service unavailable: {e}'}, status=503)

        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=400)

        # ── Step 2: Fetch book details & snapshot prices ───────────────────────
        print(f"[order-service] Step 2: Fetching book prices (snapshot)")
        order_items_data = []
        total_amount = decimal.Decimal('0')

        for item in cart_items:
            book_id = item['book_id']
            quantity = item['quantity']
            try:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}/")
                _log(f"fetch_book_{book_id}", book_resp)
                book = book_resp.json()
                unit_price = decimal.Decimal(str(book['price']))
                total_amount += unit_price * quantity
                order_items_data.append({
                    'book_id': book_id,
                    'book_title': book.get('title', ''),
                    'quantity': quantity,
                    'unit_price': unit_price,
                })
            except Exception as e:
                return Response({'error': f'book-service error for book {book_id}: {e}'}, status=503)

        # Add shipping fee to total
        total_amount += shipping_fee

        # ── Step 3: Create Order in DB (status=pending) ────────────────────────
        print(f"[order-service] Step 3: Creating Order (pending) - total: {total_amount}")
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total_amount,
            status='pending',
            shipping_address=shipping_address,
            shipping_fee=shipping_fee,
            shipping_method=shipping_method
        )
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # ── Step 4: Call pay-service ───────────────────────────────────────────
        print(f"[order-service] Step 4: Calling pay-service for order {order.id}")
        try:
            pay_resp = requests.post(f"{PAY_SERVICE_URL}/payments/", json={
                'order_id': order.id,
                'customer_id': customer_id,
                'amount': str(total_amount),
                'method': payment_method,
            })
            _log("pay_service", pay_resp)
            payment_data = pay_resp.json()
        except Exception as e:
            order.status = 'failed'
            order.save()
            return Response({'error': f'pay-service unavailable: {e}'}, status=503)

        if payment_data.get('status') != 'success':
            order.status = 'failed'
            order.save()
            print(f"[order-service] Payment FAILED for order {order.id}")
            return Response({
                'error': 'Payment failed',
                'payment': payment_data,
                'order_id': order.id
            }, status=402)

        # Payment succeeded → update order status to processing
        order.status = 'processing'
        order.save()
        print(f"[order-service] Payment SUCCESS for order {order.id} - txn: {payment_data.get('transaction_id')}")

        # ── Step 5: Call ship-service ──────────────────────────────────────────
        print(f"[order-service] Step 5: Calling ship-service for order {order.id}")
        try:
            ship_resp = requests.post(f"{SHIP_SERVICE_URL}/shipments/", json={
                'order_id': order.id,
                'customer_id': customer_id,
                'address': shipping_address or 'Default Address',
                'shipping_method': shipping_method,
            })
            _log("ship_service", ship_resp)
            shipment_data = ship_resp.json()
        except Exception as e:
            # Ship failure doesn't roll back payment, just log it
            print(f"[order-service] ship-service error: {e}")
            shipment_data = {}

        print(f"[order-service] Order {order.id} COMPLETED - shipment: {shipment_data.get('tracking_code')}")

        # Return full checkout summary
        return Response({
            'message': 'Order placed successfully!',
            'order': OrderSerializer(order).data,
            'payment': {
                'transaction_id': payment_data.get('transaction_id'),
                'method': payment_data.get('method'),
                'status': payment_data.get('status'),
            },
            'shipment': {
                'tracking_code': shipment_data.get('tracking_code'),
                'estimated_delivery': shipment_data.get('estimated_delivery'),
                'status': shipment_data.get('status'),
            }
        }, status=201)

    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            orders = Order.objects.filter(customer_id=customer_id).order_by('-created_at')
        else:
            orders = Order.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class OrderDetail(APIView):
    """
    GET   /orders/<id>/        → Order detail
    PATCH /orders/<id>/status/ → Update order status (internal)
    """
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)


class OrderStatusUpdate(APIView):
    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            new_status = request.data.get('status')
            valid = [s[0] for s in Order.STATUS_CHOICES]
            if new_status not in valid:
                return Response({'error': f'Invalid status. Must be one of: {valid}'}, status=400)
            order.status = new_status
            order.save()
            print(f"[order-service] Order {pk} status updated to: {new_status}")
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

class CheckPurchase(APIView):
    """
    GET /api/check-purchase/?customer_id={id}&book_id={id}
    Returns {"has_purchased": true/false} checking all items of this customer's orders.
    """
    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        book_id = request.query_params.get('book_id')
        
        if not customer_id or not book_id:
            return Response({'error': 'customer_id and book_id are required'}, status=400)
            
        has_purchased = OrderItem.objects.filter(
            order__customer_id=customer_id,
            book_id=book_id
        ).exists()
        
        return Response({'has_purchased': has_purchased})
