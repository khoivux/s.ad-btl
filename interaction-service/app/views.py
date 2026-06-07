import pymongo
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

client = pymongo.MongoClient(settings.MONGO_URL)
db = client['interaction_db']
logs_collection = db['logs']
search_collection = db['search_history']
chat_collection = db['chat_messages']
wishlist_collection = db['wishlist']

class LogInteraction(APIView):
    def post(self, request):
        data = request.data
        user_id = data.get('user_id') or data.get('customer_id')
        if not user_id or not data.get('action_type'):
            return Response({"error": "Missing user_id or action_type"}, status=status.HTTP_400_BAD_REQUEST)
        
        log_doc = {
            "user_id": int(user_id),
            "action": data['action_type'],
            "product_id": data.get('product_id') or data.get('book_id'),
            "timestamp": datetime.utcnow()
        }
        logs_collection.insert_one(log_doc)
        return Response({"status": "logged"}, status=status.HTTP_201_CREATED)

class GetUserLogs(APIView):
    def get(self, request, user_id):
        logs = list(logs_collection.find({"user_id": int(user_id)}).sort("timestamp", -1))
        for log in logs:
            log['_id'] = str(log['_id'])
        return Response(logs)

class SearchHistoryView(APIView):
    def post(self, request, user_id):
        query = request.data.get('query')
        if not query:
            return Response({"error": "Query required"}, status=400)
        
        doc = {
            "user_id": int(user_id),
            "query": query,
            "timestamp": datetime.utcnow()
        }
        search_collection.insert_one(doc)
        return Response({"status": "recorded"}, status=201)

    def get(self, request, user_id):
        history = list(search_collection.find({"user_id": int(user_id)}).sort("timestamp", -1))
        for h in history:
            h['_id'] = str(h['_id'])
        return Response(history)

class ChatMessageView(APIView):
    def post(self, request, user_id):
        role = request.data.get('role')
        content = request.data.get('content')
        if not role or not content:
            return Response({"error": "Role and content required"}, status=400)
        
        doc = {
            "user_id": int(user_id),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        chat_collection.insert_one(doc)
        return Response({"status": "sent"}, status=201)

    def get(self, request, user_id):
        messages = list(chat_collection.find({"user_id": int(user_id)}).sort("timestamp", 1))
        for m in messages:
            m['_id'] = str(m['_id'])
        return Response(messages)

class WishlistView(APIView):
    def post(self, request, user_id):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "product_id required"}, status=400)
        
        # Check if already in wishlist
        existing = wishlist_collection.find_one({"user_id": int(user_id), "product_id": int(product_id)})
        if existing:
            return Response({"status": "already_in_wishlist"}, status=200)
        
        doc = {
            "user_id": int(user_id),
            "product_id": int(product_id),
            "added_at": datetime.utcnow()
        }
        wishlist_collection.insert_one(doc)
        return Response({"status": "added"}, status=201)

    def get(self, request, user_id):
        wishlist = list(wishlist_collection.find({"user_id": int(user_id)}).sort("added_at", -1))
        for item in wishlist:
            item['_id'] = str(item['_id'])
        return Response(wishlist)

    def delete(self, request, user_id):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "product_id required"}, status=400)
        
        wishlist_collection.delete_one({"user_id": int(user_id), "product_id": int(product_id)})
        return Response({"status": "removed"}, status=200)
