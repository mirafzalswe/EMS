from django.urls import path
from . import views

app_name = 'motivation'

urlpatterns = [
    path('admin-store/', views.admin_store, name='admin_store'),
    path('create/', views.product_create, name='product_create'),
    path('student-store/', views.student_store, name='student_store'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('admin-cart/', views.admin_cart, name='admin_cart'),
    path('admin-students/', views.admin_students, name='admin_students'),
    path('admin-purchases/', views.admin_purchases, name='admin_purchases'),
]