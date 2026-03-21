from rest_framework.views import APIView
from rest_framework.response import Response
from .logic import get_recommendations

class RecommendationApiView(APIView):
    """
    API View to get personalized book recommendations.
    Accepts an optional customer_id in the URL or query params.
    """
    def get(self, request, customer_id=None):
        # 1. Get customer ID (from URL or query param or anonymous)
        if not customer_id:
            customer_id = request.query_params.get('customer_id')
        
        # 2. Convert to int if possible
        try:
            cid = int(customer_id) if customer_id else None
        except (TypeError, ValueError):
            cid = None

        # 3. Call recommendation logic
        recommendations = get_recommendations(cid)
        
        # 4. Return as JSON
        return Response({
            'customer_id': cid,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
