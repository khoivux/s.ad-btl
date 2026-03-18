from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import Shipment, ShippingMethod
from .serializers import ShipmentSerializer, ShippingMethodSerializer

class ShipmentCreate(APIView):
    """
    POST /shipments/ → Create a new shipment.
    GET  /shipments/<id>/ → Track shipment.
    """
    def post(self, request):
        serializer = ShipmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        # Calculate ETA based on shipping method
        method_slug = request.data.get('shipping_method', 'standard')
        try:
            method_obj = ShippingMethod.objects.get(id_slug=method_slug)
            shipment = serializer.save()
            shipment.estimated_delivery = timezone.now() + timedelta(days=method_obj.estimated_days)
            # Add prefix to tracking code based on method
            chars = string.ascii_uppercase + string.digits
            prefix = method_slug[:2].upper()
            shipment.tracking_code = f"VN-{prefix}-" + ''.join(random.choices(chars, k=8))
            shipment.save()
        except ShippingMethod.DoesNotExist:
            shipment = serializer.save()

        print(f"[ship-service] Shipment #{shipment.id} for Order {shipment.order_id} "
              f"| Tracking: {shipment.tracking_code} "
              f"| Method: {shipment.shipping_method}")
        return Response(ShipmentSerializer(shipment).data, status=201)


class ShipmentDetail(APIView):
    def get(self, request, pk):
        try:
            shipment = Shipment.objects.get(pk=pk)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)


class ShipmentStatusUpdate(APIView):
    """
    PATCH /shipments/<id>/status/ → Update shipment status (e.g., by delivery staff).
    """
    def patch(self, request, pk):
        try:
            shipment = Shipment.objects.get(pk=pk)
            new_status = request.data.get('status')
            valid = [s[0] for s in Shipment.STATUS_CHOICES]
            if new_status not in valid:
                return Response({'error': f'Invalid status. Must be: {valid}'}, status=400)
            shipment.status = new_status
            shipment.save()
            print(f"[ship-service] Shipment {pk} status updated to: {new_status}")
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)

class ShippingMethodList(APIView):
    """
    GET /shipping-methods/ → Returns available shipping options and fees.
    """
    def get(self, request):
        methods = ShippingMethod.objects.all()
        # If no methods in DB, initialize them automatically
        if not methods.exists():
            default_data = [
                {'id_slug': 'economy', 'name': 'Giao hàng Tiết kiệm', 'base_fee': 1.0, 'free_threshold': 30.0, 'estimated_days': 7, 'description': '5 - 7 ngày'},
                {'id_slug': 'standard', 'name': 'Giao hàng Tiêu chuẩn', 'base_fee': 2.5, 'free_threshold': 70.0, 'estimated_days': 4, 'description': '3 - 5 ngày'},
                {'id_slug': 'fast', 'name': 'Giao hàng Nhanh', 'base_fee': 5.0, 'free_threshold': 150.0, 'estimated_days': 2, 'description': '1 - 2 ngày'},
                {'id_slug': 'instant', 'name': 'Giao hàng Hỏa tốc', 'base_fee': 10.0, 'free_threshold': None, 'estimated_days': 0, 'description': '2 - 4 giờ (TP.HCM)'},
            ]
            for d in default_data:
                ShippingMethod.objects.create(**d)
            methods = ShippingMethod.objects.all()
        
        serializer = ShippingMethodSerializer(methods, many=True)
        return Response(serializer.data)

class ShipmentByOrder(APIView):
    """
    GET /shipments/order/<order_id>/ → Returns shipment details for a specific order.
    """
    def get(self, request, order_id):
        try:
            shipment = Shipment.objects.get(order_id=order_id)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Shipment not found'}, status=404)
