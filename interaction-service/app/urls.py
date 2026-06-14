from django.urls import path
from .views import LogInteraction, GetUserLogs, SearchHistoryView, ChatMessageView, WishlistView

urlpatterns = [
    path('logs/', LogInteraction.as_view(), name='log_interaction'),
    path('logs/user/<int:user_id>/', GetUserLogs.as_view(), name='get_user_logs'),
    path('search-history/<int:user_id>/', SearchHistoryView.as_view(), name='search_history'),
    path('chat-messages/<int:user_id>/', ChatMessageView.as_view(), name='chat_messages'),
    path('wishlist/<int:user_id>/', WishlistView.as_view(), name='wishlist'),
]
