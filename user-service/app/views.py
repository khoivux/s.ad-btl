from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Address, MembershipLevel, LoyaltyWallet, PointTransaction
from .serializers import UserSerializer, AddressSerializer, LoyaltyWalletSerializer, MembershipLevelSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from .decorators import role_required
from rest_framework_simplejwt.tokens import RefreshToken

import requests
CART_SERVICE_URL = "http://cart-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8000"

@method_decorator(csrf_exempt, name='dispatch')
class UserListCreate(APIView):
    @method_decorator(role_required(['ADMIN']))
    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        data = request.data
        username = data.get('username') or data.get('email')
        if not username:
            return Response({"error": "Username or email is required"}, status=400)
            
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)
        
        email = data.get('email', '')
        if email and User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=400)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=data.get('password', '123456'),
            role=data.get('role', 'CUSTOMER'),
            phone_number=data.get('phone_number', '')
        )
        
        # If it's a customer, auto-create Loyalty Wallet
        if user.role == 'CUSTOMER':
            bronze = MembershipLevel.objects.filter(name='Bronze').first()
            LoyaltyWallet.objects.get_or_create(user=user, defaults={'current_level': bronze})
            
            try:
                requests.post(f"{CART_SERVICE_URL}/carts/", json={"customer_id": user.id})
            except Exception:
                pass
        
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        user_data['access'] = str(refresh.access_token)
        user_data['refresh'] = str(refresh)
        return Response(user_data, status=201)

@method_decorator(csrf_exempt, name='dispatch')
class UserDetail(APIView):
    @method_decorator(role_required(['ADMIN', 'STAFF', 'CUSTOMER']))
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Update password if provided
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        # Try finding by username first, then email
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(email=username).first()
            
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data
            user_data['access'] = str(refresh.access_token)
            user_data['refresh'] = str(refresh)
            return Response(user_data)
            
        return Response({"error": "Invalid credentials"}, status=401)

@method_decorator(csrf_exempt, name='dispatch')
class AddressListCreate(APIView):
    @method_decorator(role_required(['ADMIN', 'STAFF', 'CUSTOMER']))
    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        addresses = user.addresses.all()
        return Response(AddressSerializer(addresses, many=True).data)

    @method_decorator(role_required(['ADMIN', 'CUSTOMER']))
    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        data = request.data.copy()
        data['user'] = user_id
        serializer = AddressSerializer(data=data)
        if serializer.is_valid():
            address = serializer.save()
            return Response(AddressSerializer(address).data, status=201)
        return Response(serializer.errors, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class AddressDetail(APIView):
    def _get_address(self, user_id, pk):
        try:
            return Address.objects.get(pk=pk, user_id=user_id)
        except Address.DoesNotExist:
            return None

    def put(self, request, user_id, pk):
        address = self._get_address(user_id, pk)
        if not address:
            return Response({'error': 'Not found'}, status=404)
        data = request.data.copy()
        data['user'] = user_id
        serializer = AddressSerializer(address, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, user_id, pk):
        address = self._get_address(user_id, pk)
        if not address:
            return Response({'error': 'Not found'}, status=404)
        address.delete()
        return Response(status=204)

    def patch(self, request, user_id, pk):
        """Set this address as default."""
        address = self._get_address(user_id, pk)
        if not address:
            return Response({'error': 'Not found'}, status=404)
        address.is_default = True
        address.save()
        return Response(AddressSerializer(address).data)

@method_decorator(csrf_exempt, name='dispatch')
class WalletDetail(APIView):
    @method_decorator(role_required(['ADMIN', 'STAFF', 'CUSTOMER']))
    def get(self, request, user_id):
        try:
            wallet = LoyaltyWallet.objects.get(user_id=user_id)
            return Response(LoyaltyWalletSerializer(wallet).data)
        except LoyaltyWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class AddPointsView(APIView):
    def post(self, request, user_id):
        amount = int(request.data.get('amount') or 0)
        desc = request.data.get('description') or 'Purchase reward'
        txn_type = request.data.get('transaction_type') or ('EARN' if amount >= 0 else 'SPEND')
        
        try:
            wallet = LoyaltyWallet.objects.get(user_id=user_id)
            wallet.usable_points += amount
            if amount > 0:
                wallet.accumulated_points += amount
            
            levels = MembershipLevel.objects.all().order_by('-min_points')
            for level in levels:
                if wallet.accumulated_points >= level.min_points:
                    wallet.current_level = level
                    break
            wallet.save()
            PointTransaction.objects.create(wallet=wallet, amount=amount, transaction_type=txn_type, description=desc)
            return Response(LoyaltyWalletSerializer(wallet).data)
        except LoyaltyWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class PointTransactionListView(APIView):
    def get(self, request, user_id):
        try:
            wallet = LoyaltyWallet.objects.get(user_id=user_id)
            transactions = wallet.transactions.all().order_by('-created_at')
            
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            
            from .serializers import PointTransactionSerializer
            serializer = PointTransactionSerializer(transactions[start:end], many=True)
            
            return Response({
                'transactions': serializer.data,
                'has_more': transactions.count() > end,
                'total': transactions.count()
            })
        except LoyaltyWallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)

@method_decorator(csrf_exempt, name='dispatch')
class MembershipLevelList(APIView):
    def get(self, request):
        levels = MembershipLevel.objects.all().order_by('id')
        return Response(MembershipLevelSerializer(levels, many=True).data)

# Staff Specific Proxy Views (inherited from staff-service)
@method_decorator(csrf_exempt, name='dispatch')
class StaffProductManager(APIView):
    @method_decorator(role_required(['ADMIN', 'STAFF']))
    def post(self, request):
        r = requests.post(f"{PRODUCT_SERVICE_URL}/products/", json=request.data)
        try:
            return Response(r.json(), status=r.status_code)
        except:
            return Response({"error": r.text}, status=r.status_code)

@method_decorator(csrf_exempt, name='dispatch')
class StaffProductDetailManager(APIView):
    @method_decorator(role_required(['ADMIN', 'STAFF']))
    def put(self, request, pk):
        r = requests.put(f"{PRODUCT_SERVICE_URL}/products/{pk}/", json=request.data)
        try:
            return Response(r.json(), status=r.status_code)
        except:
            return Response({"error": r.text}, status=r.status_code)

    @method_decorator(role_required(['ADMIN', 'STAFF']))
    def delete(self, request, pk):
        r = requests.delete(f"{PRODUCT_SERVICE_URL}/products/{pk}/")
        if r.status_code == 204:
            return Response({'status': 'deleted'})
        return Response({'error': 'Failed to delete'}, status=r.status_code)