from django.db import models

# In a microservices architecture, this service stays "Lean".
# It doesn't store raw review data (that belongs to comment-rate-service).
# We only use functions to process external data on-the-fly.
