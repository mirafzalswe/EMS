from django.urls import path

from .views import income_chart

urlpatterns = [
    path('income-chart/', income_chart, name='income_chart'),
]
 
    
