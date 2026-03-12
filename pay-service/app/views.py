from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer

class PaymentCreate(APIView):
    """
    POST /payments/ → Process a payment (mock gateway).
    GET  /payments/<id>/ → Get payment status.
    """
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # ── Mock Payment Logic ──────────────────────────────────────────────
        # In production: call Stripe/VNPay/MoMo SDK here.
        # For demo: all COD always succeed; BANK_TRANSFER/MOMO have 90% success rate.
        import random
        method = request.data.get('method', 'COD')
        if method == 'COD':
            payment_status = 'success'
        else:
            # 90% success rate for online payment
            payment_status = 'success' if random.random() < 0.9 else 'failed'

        payment = serializer.save(status=payment_status)
        print(f"[pay-service] Payment #{payment.id} for Order {payment.order_id} "
              f"| Method: {method} | Status: {payment_status} "
              f"| TXN: {payment.transaction_id}")

        return Response(PaymentSerializer(payment).data, status=201)


class PaymentDetail(APIView):
    def get(self, request, pk):
        try:
            payment = Payment.objects.get(pk=pk)
            return Response(PaymentSerializer(payment).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)
