from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:book_id>/', views.book_detail_view, name='book_detail'),
    path('api/books/<int:book_id>/reviews/', views.book_review_submit, name='book_review_submit'),
    path('search/', views.search_view, name='search'),
    path('login/', views.login_view, name='login'),

    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('carts/<int:customer_id>/', views.view_cart, name='view_cart'),
    path('api/carts/items/<int:item_id>/', views.modify_cart_item, name='modify_cart_item'),
    path('api/carts/items/', views.add_cart_item, name='add_cart_item'),
    # Checkout & Orders
    path('checkout/', views.checkout_page_view, name='checkout_page'),
    path('api/checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.order_history_view, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    # Address API proxy
    path('api/addresses/<int:customer_id>/', views.address_list_create, name='address_list'),
    path('api/addresses/<int:customer_id>/<int:pk>/', views.address_detail, name='address_detail'),
    # Staff routes
    path('staff/login/', views.staff_login_view, name='staff_login'),
    path('staff/dashboard/', views.staff_dashboard_view, name='staff_dashboard'),
    path('staff/logout/', views.staff_logout_view, name='staff_logout'),
    path('staff/books/add/', views.staff_add_book, name='staff_add_book'),
    path('staff/books/<int:pk>/update/', views.staff_update_book, name='staff_update_book'),
    path('staff/books/<int:pk>/delete/', views.staff_delete_book, name='staff_delete_book'),
]

