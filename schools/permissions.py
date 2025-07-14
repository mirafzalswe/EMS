from rest_framework import permissions

class IsSchoolStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.is_teacher or 
            request.user.is_staff
        )

class IsSchoolAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.is_staff
        ) 