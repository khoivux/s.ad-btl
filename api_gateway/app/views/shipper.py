import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .base import BaseProxyView

SHIP_SERVICE_URL = "http://ship-service:8000"

class ShipperDashboardView(BaseProxyView):
    def get(self, request):
        return render(request, "shipper_dashboard.html")

@method_decorator(csrf_exempt, name='dispatch')
class ShipperShipmentsApiView(BaseProxyView):
    service_url = SHIP_SERVICE_URL

    def get(self, request, filter_type):
        if filter_type == 'available':
            r = self.proxy_request(request, "shipments/available/", method="GET")
        elif filter_type == 'active':
            r = self.proxy_request(request, "shipments/active/", method="GET")
        else:
            return JsonResponse({'error': 'Invalid filter'}, status=400)
            
        if not r: return JsonResponse({'error': 'Service Unavailable'}, status=503)
        return JsonResponse(r.json(), safe=False, status=r.status_code)

@method_decorator(csrf_exempt, name='dispatch')
class ShipperStatusUpdateApiView(BaseProxyView):
    service_url = SHIP_SERVICE_URL

    def patch(self, request, pk):
        try:
            data = json.loads(request.body)
            r = self.proxy_request(request, f"shipments/{pk}/status/", method="PATCH", payload=data)
            if not r: return JsonResponse({'error': 'Service Unavailable'}, status=503)
            return JsonResponse(r.json(), status=r.status_code)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
