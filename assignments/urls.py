from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:group_id>/', views.create_assignment, name='assigment_create'),
    path('list/<int:group_id>/', views.assignment_list, name='assignment_list'),
    path('<int:assignment_id>/detail/', views.assignment_detail, name='assignment_detail'),
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
] 