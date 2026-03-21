from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.norm_url_path if hasattr(admin.site, 'norm_url_path') else admin.site.urls), # Standard handling
    path('api/', include('app.urls')),
    path('', include('app.urls')),
]
