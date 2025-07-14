# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Кастомная админка для модели User
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Личная информация'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'birthday', 'avatar', 'bio')
        }),
        (_('Роли и доступ'), {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Дополнительно для преподавателей'), {
            'fields': ('specialization', 'experience'),
        }),
        (_('Дополнительно для учеников'), {
            'fields': ('parent',),
        }),
        (_('Уведомления'), {
            'fields': ('email_notifications', 'sms_notifications')
        }),
        (_('Даты'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'user_type'
            ),
        }),
    )

    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)
