from rest_framework import permissions
from django.db.models import Q

class IsMessageParticipant(permissions.BasePermission):
    """
    Разрешает доступ только если пользователь является отправителем или получателем сообщения.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Проверяем, является ли пользователь отправителем
        if obj.sender == user:
            return True
        
        # Проверяем, является ли пользователь получателем
        if user in obj.recipients.all():
            # Для удаленных сообщений ограничиваем доступ
            recipient_status = obj.message_recipients.filter(recipient=user).first()
            if recipient_status and recipient_status.is_deleted:
                # Для удаленных сообщений разрешаем только чтение и восстановление
                return request.method in permissions.SAFE_METHODS or \
                       view.action == 'restore'
            return True
        
        return False

class IsAnnouncementCreator(permissions.BasePermission):
    """
    Разрешает полный доступ создателям объявлений и доступ на чтение получателям.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Создатель объявления имеет полный доступ
        if obj.message.sender == user:
            return True
        
        # Получатели имеют доступ только на чтение
        if user in obj.message.recipients.all() or \
           (obj.message.school and user.schools.filter(id=obj.message.school.id).exists()) or \
           (obj.message.branch and user.branches.filter(id=obj.message.branch.id).exists()) or \
           (obj.message.group and user.groups.filter(id=obj.message.group.id).exists()):
            return request.method in permissions.SAFE_METHODS
        
        return False

class IsChatGroupMember(permissions.BasePermission):
    """
    Разрешает доступ только членам чат-группы, с расширенными правами для создателя.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Проверяем членство в группе
        is_member = user in obj.members.all()
        
        # Создатель имеет полные права
        if obj.created_by == user:
            return True
        
        # Члены могут просматривать и отправлять сообщения
        if is_member:
            # Разрешаем чтение и некоторые действия
            if request.method in permissions.SAFE_METHODS or \
               view.action in ['send_message', 'leave_group']:
                return True
        
        return False

class IsNotificationRecipient(permissions.BasePermission):
    """
    Разрешает доступ только получателю уведомления.
    """
    def has_object_permission(self, request, view, obj):
        # Только получатель уведомления имеет к нему доступ
        return obj.user == request.user