# scheduling/urls.py

from django.urls import path
from . import views

# Create a router and register our viewsets with it
app_name="scheduling"
# The API URLs are determined automatically by the router
urlpatterns = [
    path('add_schedule_group/<int:pk>/', views.add_schedule_group, name='add_schedule_group'),
]

