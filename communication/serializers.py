from rest_framework import serializers
from django.utils import timezone
from users.serializers import UserLightSerializer
from .models import (
    Message, MessageRecipient, MessageAttachment, 
    Announcement, Notification, ChatGroup, MessageStatus
)

# Serializers for communication app

class MessageAttachmentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вложений сообщений.
    """
    class Meta:
        model = MessageAttachment
        fields = ['id', 'file', 'file_name', 'file_size', 'content_type', 'uploaded_at']
        read_only_fields = ['file_size', 'content_type', 'uploaded_at']
    
    def create(self, validated_data):
        """
        Автоматически определяем размер и тип файла при создании.
        """
        file = validated_data.get('file')
        if file:
            validated_data['file_size'] = file.size
            validated_data['content_type'] = file.content_type
        return super().create(validated_data)

class MessageRecipientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для статусов сообщений у получателей.
    """
    recipient_details = UserLightSerializer(source='recipient', read_only=True)
    
    class Meta:
        model = MessageRecipient
        fields = ['id', 'recipient', 'recipient_details', 'status', 'read_at', 'is_starred', 'is_deleted']
        read_only_fields = ['read_at']
    
    def update(self, instance, validated_data):
        """
        Обновляем время прочтения при изменении статуса на "прочитано".
        """
        if 'status' in validated_data and validated_data['status'] == MessageStatus.READ and instance.status != MessageStatus.READ:
            validated_data['read_at'] = timezone.now()
        return super().update(instance, validated_data)

class MessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор для сообщений с дополнительными данными.
    """
    sender_details = UserLightSerializer(source='sender', read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    recipient_statuses = MessageRecipientSerializer(source='message_recipients', many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_details', 'subject', 'content', 
            'message_type', 'group', 'school', 'branch', 'created_at', 
            'updated_at', 'is_draft', 'parent', 'attachments', 
            'recipient_statuses', 'reply_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_reply_count(self, obj):
        """
        Получаем количество ответов на сообщение.
        """
        return obj.replies.count()
    
    def create(self, validated_data):
        """
        Создаем сообщение с получателями.
        """
        recipients_data = self.context.get('recipients', [])
        attachments_data = self.context.get('attachments', [])
        
        message = Message.objects.create(**validated_data)
        
        # Создаем связи с получателями
        for recipient_id in recipients_data:
            MessageRecipient.objects.create(
                message=message,
                recipient_id=recipient_id
            )
        
        # Сохраняем вложения
        for attachment_data in attachments_data:
            MessageAttachment.objects.create(message=message, **attachment_data)
            
        return message

class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания сообщений с получателями и вложениями.
    """
    recipients = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    attachments = MessageAttachmentSerializer(many=True, required=False)
    
    class Meta:
        model = Message
        fields = [
            'sender', 'recipients', 'subject', 'content', 
            'message_type', 'group', 'school', 'branch', 
            'is_draft', 'parent', 'attachments'
        ]
    
    def create(self, validated_data):
        recipients_data = validated_data.pop('recipients', [])
        attachments_data = validated_data.pop('attachments', [])
        
        # Создаем сообщение
        message = Message.objects.create(**validated_data)
        
        # Создаем связи с получателями
        for recipient_id in recipients_data:
            MessageRecipient.objects.create(
                message=message,
                recipient_id=recipient_id
            )
        
        # Сохраняем вложения
        for attachment_data in attachments_data:
            MessageAttachment.objects.create(message=message, **attachment_data)
            
        return message

class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Сериализатор для объявлений.
    """
    message = MessageSerializer(read_only=True)
    message_data = MessageCreateSerializer(write_only=True)
    
    class Meta:
        model = Announcement
        fields = ['id', 'message', 'message_data', 'expires_at', 'is_pinned', 'priority']
    
    def create(self, validated_data):
        message_data = validated_data.pop('message_data')
        
        # Устанавливаем тип сообщения как объявление
        message_data['message_type'] = 'announcement'
        
        # Используем MessageCreateSerializer для создания сообщения
        message_serializer = MessageCreateSerializer(data=message_data, context=self.context)
        message_serializer.is_valid(raise_exception=True)
        message = message_serializer.save()
        
        # Создаем объявление
        announcement = Announcement.objects.create(message=message, **validated_data)
        return announcement

class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для уведомлений.
    """
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'content', 'link', 'is_read', 'created_at']
        read_only_fields = ['created_at']

class ChatGroupSerializer(serializers.ModelSerializer):
    """
    Сериализатор для групповых чатов.
    """
    members_details = UserLightSerializer(source='members', many=True, read_only=True)
    created_by_details = UserLightSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = ChatGroup
        fields = [
            'id', 'name', 'description', 'members', 'members_details',
            'created_by', 'created_by_details', 'school', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']

class MessageListSerializer(serializers.ModelSerializer):
    """
    Облегченный сериализатор для списка сообщений.
    """
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'subject', 
            'message_type', 'created_at', 'unread_count'
        ]
    
    def get_unread_count(self, obj):
        """
        Получаем количество непрочитанных сообщений в цепочке.
        """
        user = self.context.get('request').user
        if not user:
            return 0
            
        # Учитываем как само сообщение, так и все ответы на него
        base_query = MessageRecipient.objects.filter(
            recipient=user,
            status__in=[MessageStatus.SENT, MessageStatus.DELIVERED],
            is_deleted=False
        )
        
        thread_ids = [obj.id] + list(obj.replies.values_list('id', flat=True))
        return base_query.filter(message_id__in=thread_ids).count()