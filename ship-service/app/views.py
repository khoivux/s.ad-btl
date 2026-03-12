from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Shipment
from .serializers import ShipmentSerializer

class ShipmentCreate(APIView):
    """
    POST /shipments/ → Create a new shipment.
    GET  /shipments/<id>/ → Track shipment.
    """
    def post(self, request):
        serializer = ShipmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        shipment = serializer.save()
        print(f"[ship-service] Shipment #{shipment.id} for Order {shipment.order_id} "
              f"| Tracking: {shipment.tracking_code} "
              f"| ETA: {shipment.estimated_delivery}")
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
        methods = [
            {
                'id': 'standard',
                'name': 'Standard Shipping',
                'description': '3-5 business days',
                'fee': 2.00
            },
            {
                'id': 'express',
                'name': 'Express Shipping',
                'description': '1-2 business days',
                'fee': 5.00
            }
        ]
        return Response(methods)

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
