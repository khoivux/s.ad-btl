from django.urls import path
from .views import RecommendationApiView

urlpatterns = [
    path('recommendations/', RecommendationApiView.as_view(), name='recommendation_list'),
    path('recommendations/<int:customer_id>/', RecommendationApiView.as_view(), name='recommendation_personalized'),
]
