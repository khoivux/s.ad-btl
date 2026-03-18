from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, Voucher, CustomerVoucher
from .serializers import OrderSerializer, VoucherSerializer, CustomerVoucherSerializer
import requests
import decimal
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

CART_SERVICE_URL = "http://cart-service:8000"
BOOK_SERVICE_URL = "http://book-service:8000"
PAY_SERVICE_URL  = "http://pay-service:8000"
SHIP_SERVICE_URL = "http://ship-service:8000"
CUSTOMER_SERVICE_URL = "http://customer-service:8000"

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

        # ── Step 2.5: Loyalty & Discounts ────────────────────────────────────
        print(f"[order-service] Step 2.5: Checking loyalty for customer {customer_id}")
        membership_discount = decimal.Decimal('0')
        points_to_generate = int(total_amount * 10)  # 1$ = 10 pts
        
        try:
            cust_resp = requests.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/")
            if cust_resp.status_code == 200:
                customer_data = cust_resp.json()
                wallet = customer_data.get('wallet')
                if wallet and wallet.get('current_level'):
                    tier_discount = wallet['current_level']['discount_percentage']
                    if tier_discount > 0:
                        membership_discount = (total_amount * decimal.Decimal(str(tier_discount))) / 100
                        print(f"[order-service] Tier discount applied: {tier_discount}% (-{membership_discount})")
        except Exception as e:
            print(f"[order-service] Could not fetch loyalty info: {e}")

        # ── Step 2.6: Voucher Handling ─────────────────────────────────────────
        voucher_discount = decimal.Decimal('0')
        voucher_code = request.data.get('voucher_code', '')
        if voucher_code:
            try:
                voucher = Voucher.objects.filter(code=voucher_code, is_active=True).first()
                if not voucher:
                    return Response({'error': 'Invalid or expired voucher code.'}, status=400)

                # Check if it's a public voucher OR if the customer owns it
                is_available = False
                if voucher.is_public:
                    is_available = True
                else:
                    # Check ownership
                    ownership = CustomerVoucher.objects.filter(customer_id=customer_id, voucher=voucher, is_used=False).first()
                    if ownership:
                        is_available = True
                    else:
                        return Response({'error': 'You do not own this voucher or it was already used.'}, status=400)

                if is_available:
                    # Validate min spend
                    if total_amount >= voucher.min_spend:
                        # Validate min level
                        current_level_id = wallet.get('current_level', {}).get('id') if 'wallet' in locals() and wallet else None
                        if not voucher.min_points_level_id or (current_level_id and current_level_id >= voucher.min_points_level_id):
                            # Dedut points if any (Only for public vouchers that cost points - non-public ones are already 'paid' for)
                            if voucher.is_public and voucher.point_cost > 0:
                                spend_payload = {
                                    'points': -voucher.point_cost,
                                    'transaction_type': 'SPEND',
                                    'description': f'Used public voucher {voucher.code}'
                                }
                                spend_r = requests.post(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/add-points/", json=spend_payload)
                                if spend_r.status_code != 200:
                                    return Response({'error': 'Insufficient points to use this voucher'}, status=400)

                            if voucher.is_percentage:
                                voucher_discount = (total_amount * decimal.Decimal(str(voucher.discount_amount))) / 100
                            else:
                                voucher_discount = decimal.Decimal(str(voucher.discount_amount))
                            
                            # Mark as used if it was a CustomerVoucher
                            if not voucher.is_public:
                                ownership.is_used = True
                                ownership.used_at = django.utils.timezone.now() if 'django.utils.timezone' in locals() else None # Need import
                                # ownership.save() # I'll do this later after order creation to ensure atomicity or just do it here
                                # Better to save after order is confirmed successful OR link it to order
                                # But for now, let's just mark it.
                            
                            print(f"[order-service] Voucher applied: {voucher.code} (-{voucher_discount})")
                        else:
                            return Response({'error': 'Voucher not available for your membership level'}, status=400)
                    else:
                        return Response({'error': f'Voucher requires minimum spend of {voucher.min_spend}'}, status=400)
                else:
                    return Response({'error': 'Voucher not available.'}, status=400)
            except Exception as e:
                print(f"[order-service] Voucher processing error: {e}")

        # Final amount after discount + shipping
        final_amount = (total_amount - membership_discount - voucher_discount) + shipping_fee

        # ── Step 3: Create Order in DB (status=pending) ────────────────────────
        print(f"[order-service] Step 3: Creating Order (pending) - total: {final_amount}")
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=final_amount,
            status='pending',
            membership_discount=membership_discount,
            voucher_discount=voucher_discount,
            voucher_code=voucher_code,
            points_generated=points_to_generate,
            shipping_address=shipping_address,
            shipping_fee=shipping_fee,
            shipping_method=shipping_method
        )
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

        # Update voucher usage if applicable
        if voucher_code and 'ownership' in locals() and ownership:
            ownership.is_used = True
            ownership.order_id = order.id
            import django.utils.timezone
            ownership.used_at = django.utils.timezone.now()
            ownership.save()
            print(f"[order-service] CustomerVoucher {ownership.id} marked as used for Order {order.id}")

        # ── Step 4: Call pay-service ───────────────────────────────────────────
        print(f"[order-service] Step 4: Calling pay-service for order {order.id}")
        try:
            pay_resp = requests.post(f"{PAY_SERVICE_URL}/payments/", json={
                'order_id': order.id,
                'customer_id': customer_id,
                'amount': str(order.total_amount),
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
            
            # If delivered → Add points to customer
            if new_status == 'delivered':
                try:
                    requests.post(f"{CUSTOMER_SERVICE_URL}/customers/{order.customer_id}/wallet/add-points/", json={
                        'amount': order.points_generated,
                        'description': f"Reward for order #{order.id}"
                    })
                    print(f"[order-service] Notified customer-service to award {order.points_generated} points.")
                except Exception as e:
                    print(f"[order-service] Error awarding points: {e}")

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
class OrderCancelView(APIView):
    """
    POST /orders/<id>/cancel/ → Cancel an order if it's in pending or processing state.
    """
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            if order.status not in ['pending', 'processing']:
                return Response({'error': f'Cannot cancel order in {order.status} state.'}, status=400)
            
            order.status = 'cancelled'
            order.save()
            
            # Notify ship-service to cancel shipment if exists
            try:
                requests.patch(f"{SHIP_SERVICE_URL}/shipments/order/{pk}/status/", json={'status': 'cancelled'})
            except Exception as e:
                print(f"[order-service][cancel] Could not notify ship-service: {e}")

            print(f"[order-service] Order {pk} CANCELLED by user.")
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

class OrderDeleteView(APIView):
    """
    DELETE /orders/<id>/delete/ → Delete an order if it's in cancelled state.
    """
    def delete(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            if order.status != 'cancelled':
                return Response({'error': 'Only cancelled orders can be deleted.'}, status=400)
            
            order.delete()
            print(f"[order-service] Order {pk} DELETED.")
            return Response({'message': 'Order deleted successfully.'}, status=200)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)

class VoucherList(APIView):
    def get(self, request):
        vouchers = Voucher.objects.filter(is_active=True, is_public=True)
        return Response(VoucherSerializer(vouchers, many=True).data)

@method_decorator(csrf_exempt, name='dispatch')
class VoucherDetail(APIView):
    def get(self, request, code):
        try:
            voucher = Voucher.objects.get(code=code, is_active=True)
            return Response(VoucherSerializer(voucher).data)
        except Voucher.DoesNotExist:
            return Response({'error': 'Voucher not found'}, status=404)

class StaffVoucherListCreate(APIView):
    def get(self, request):
        vouchers = Voucher.objects.all().order_by('-created_at')
        return Response(VoucherSerializer(vouchers, many=True).data)
    
    def post(self, request):
        serializer = VoucherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class StaffVoucherDetail(APIView):
    def get_object(self, pk):
        try: return Voucher.objects.get(pk=pk)
        except Voucher.DoesNotExist: return None

    def get(self, request, pk):
        v = self.get_object(pk)
        if not v: return Response({'error': 'Not found'}, status=404)
        return Response(VoucherSerializer(v).data)

    def put(self, request, pk):
        v = self.get_object(pk)
        if not v: return Response({'error': 'Not found'}, status=404)
        serializer = VoucherSerializer(v, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        v = self.get_object(pk)
        if not v: return Response({'error': 'Not found'}, status=404)
        v.delete()
        return Response(status=204)

class RedeemVoucher(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        voucher_id = request.data.get('voucher_id')
        
        if not customer_id or not voucher_id:
            return Response({'error': 'customer_id and voucher_id are required'}, status=400)
            
        try:
            voucher = Voucher.objects.get(pk=voucher_id, is_active=True)
            
            # Check limits
            if voucher.redeemed_quantity >= voucher.max_quantity:
                return Response({'error': 'This voucher has reached its redemption limit.'}, status=400)
            
            # Check points (Call customer-service)
            if voucher.point_cost > 0:
                spend_payload = {
                    'amount': -voucher.point_cost,
                    'transaction_type': 'SPEND',
                    'description': f'Exchanged points for voucher {voucher.code}'
                }
                spend_r = requests.post(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/wallet/add-points/", json=spend_payload)
                if spend_r.status_code != 200:
                    return Response({'error': 'Insufficient points to redeem this voucher.'}, status=400)
            
            # Create ownership
            CustomerVoucher.objects.create(
                customer_id=customer_id,
                voucher=voucher
            )
            
            # Update counter
            voucher.redeemed_quantity += 1
            voucher.save()
            
            return Response({'message': 'Voucher redeemed successfully!'}, status=201)
            
        except Voucher.DoesNotExist:
            return Response({'error': 'Voucher not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class CustomerVouchersView(APIView):
    def get(self, request, customer_id):
        vouchers = CustomerVoucher.objects.filter(customer_id=customer_id).order_by('-redeemed_at')
        return Response(CustomerVoucherSerializer(vouchers, many=True).data)
