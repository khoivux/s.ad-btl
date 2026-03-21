import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .base import BaseProxyView, CustomerRequiredMixin

from django.conf import settings

CUSTOMER_SERVICE_URL = settings.CUSTOMER_SERVICE_URL
ORDER_SERVICE_URL = settings.ORDER_SERVICE_URL

@method_decorator(csrf_exempt, name='dispatch')
class WalletApiView(CustomerRequiredMixin, BaseProxyView):
    service_url = CUSTOMER_SERVICE_URL

    def get(self, request):
        # Xem ví điểm - /api/loyalty/wallet/
        customer_id = request.session['customer_id']
        r = self.proxy_request(request, f"customers/{customer_id}/wallet/", method="GET")
        if not r:
            return JsonResponse({'error': 'Service Unavailable'}, status=503)
        return JsonResponse(r.json(), safe=False, status=r.status_code)


@method_decorator(csrf_exempt, name='dispatch')
class VouchersListApiView(BaseProxyView):
    service_url = ORDER_SERVICE_URL

    def get(self, request):
        # Danh sách voucher - /api/vouchers/
        r = self.proxy_request(request, "vouchers/", method="GET")
        if not r:
            return JsonResponse({'error': 'Service Unavailable'}, status=503)
            
        if r.status_code != 200:
            return JsonResponse(r.json(), safe=False, status=r.status_code)
            
        all_vouchers = r.json()
        customer_id = request.session.get('customer_id')
        
        if customer_id:
            cv_r = self.proxy_request(request, f"vouchers/customer/{customer_id}/", method="GET")
            if cv_r and cv_r.status_code == 200:
                redeemed_ids = [cv['voucher'] for cv in cv_r.json()]
                filtered = [v for v in all_vouchers if v['id'] not in redeemed_ids]
                return JsonResponse(filtered, safe=False)
                
        return JsonResponse(all_vouchers, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class MembershipLevelsApiView(BaseProxyView):
    service_url = CUSTOMER_SERVICE_URL

    def get(self, request):
        # Cấp bậc thành viên - /api/membership-levels/
        r = self.proxy_request(request, "membership-levels/", method="GET")
        if not r:
            return JsonResponse({'error': 'Service Unavailable'}, status=503)
        return JsonResponse(r.json(), safe=False, status=r.status_code)


@method_decorator(csrf_exempt, name='dispatch')
class RedeemVoucherApiView(CustomerRequiredMixin, BaseProxyView):
    service_url = ORDER_SERVICE_URL

    def post(self, request):
        # Đổi điểm lấy voucher - /api/vouchers/redeem/
        try:
            data = json.loads(request.body)
            data['customer_id'] = request.session['customer_id']
            r = self.proxy_request(request, "vouchers/redeem/", method="POST", payload=data)
            if not r:
                return JsonResponse({'error': 'Service Unavailable'}, status=503)
            return JsonResponse(r.json(), status=r.status_code)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=503)


class CustomerVouchersApiView(CustomerRequiredMixin, BaseProxyView):
    service_url = ORDER_SERVICE_URL

    def get(self, request):
        # Voucher của tôi - /api/vouchers/customer/
        customer_id = request.session['customer_id']
        r = self.proxy_request(request, f"vouchers/customer/{customer_id}/", method="GET")
        if not r:
            return JsonResponse({'error': 'Service Unavailable'}, status=503)
        return JsonResponse(r.json(), safe=False, status=r.status_code)


class VouchersShopView(BaseProxyView):
    service_url = CUSTOMER_SERVICE_URL

    def get(self, request):
        # Cửa hàng đổi điểm - /vouchers/shop/
        if 'customer_id' not in request.session:
            return redirect('login')
            
        customer_id = request.session['customer_id']
        r = self.proxy_request(request, f"customers/{customer_id}/", method="GET")
        customer_data = r.json() if r and r.status_code == 200 else {}

        return render(request, "vouchers_shop.html", {
            "customer": customer_data,
            "customer_name": request.session.get('customer_name')
        })

class VoucherDetailApiView(BaseProxyView):
    service_url = ORDER_SERVICE_URL

    def get(self, request, code):
        # Chi tiết mã giảm giá (theo mã) - /api/vouchers/<code>/
        r = self.proxy_request(request, f"vouchers/{code}/", method="GET")
        if not r:
            return JsonResponse({'error': 'Service Unavailable'}, status=503)
        return JsonResponse(r.json(), status=r.status_code)

