# courses/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubjectViewSet, CourseViewSet, GroupViewSet, 
    EnrollmentViewSet, LearningMaterialViewSet, add_course, add_group, course_list, edit_course, delete_course
)

app_name="courses"

urlpatterns = [
    path('list/', course_list, name='course_list'),
    path('add/', add_course, name='add_course'),
    path('group/add/', add_group, name='add_group'),
    path('edit/<int:pk>/', edit_course, name='edit_course'),
    path('delete/<int:pk>/', delete_course, name='delete_course'),
]   