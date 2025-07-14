# users/permissions.py

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Разрешение только для администраторов
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_admin


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение для владельца объекта или администратора
    """

    def has_object_permission(self, request, view, obj):
        # Администратор может делать что угодно
        if request.user.is_admin:
            return True

        # Если объект - пользователь, проверяем совпадение с текущим пользователем
        if hasattr(obj, 'id'):
            return obj.id == request.user.id

        # Если у объекта есть поле 'user', проверяем совпадение с текущим пользователем
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsTeacherOrAdmin(permissions.BasePermission):
    """
    Разрешение для преподавателей или администраторов
    """

    def has_permission(self, request, view):
        return request.user and (request.user.is_teacher or request.user.is_admin)