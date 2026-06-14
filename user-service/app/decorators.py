from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def role_required(allowed_roles):
    """
    Decorator for views that checks whether the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated and has the required role
            if not request.user or not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.role not in allowed_roles:
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
