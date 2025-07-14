# schools/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolViewSet, BranchViewSet, ClassroomViewSet, SchoolStaffAssignmentViewSet, SchoolManagementView
)

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'staff-assignments', SchoolStaffAssignmentViewSet)

urlpatterns = [
    path('manage/', SchoolManagementView.as_view(), name='school_management'),
    path('', include(router.urls)),
]