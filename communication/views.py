from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Message, MessageRecipient, MessageAttachment, 
    Announcement, Notification, ChatGroup, MessageStatus
)
from .serializers import (
    MessageSerializer, MessageCreateSerializer, MessageListSerializer,
    MessageRecipientSerializer, MessageAttachmentSerializer, 
    AnnouncementSerializer, NotificationSerializer, ChatGroupSerializer
)
from .permissions import (
    IsMessageParticipant, IsAnnouncementCreator, 
    IsChatGroupMember, IsNotificationRecipient
)

class MessageViewSet(viewsets.ModelViewSet):
    """
    API для работы с сообщениями.
    """
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['message_type', 'group', 'school', 'branch', 'is_draft']
    search_fields = ['subject', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Возвращает сообщения, связанные с текущим пользователем.
        """
        user = self.request.user
        
        # Получаем ID родительского сообщения из query params для фильтрации по цепочке
        parent_id = self.request.query_params.get('parent_id')
        
        # Базовый запрос для сообщений пользователя
        base_query = Message.objects.filter(
            Q(sender=user) |  # Отправленные пользователем
            Q(recipients=user, message_recipients__is_deleted=False)  # Полученные и не удаленные
        ).distinct()
        
        # Фильтруем по родительскому сообщению для цепочки или только корневые сообщения
        if parent_id:
            if parent_id == 'null':  # Если нужны только корневые сообщения
                return base_query.filter(parent__isnull=True)
            else:
                # Включаем как родительское сообщение, так и все его ответы
                return base_query.filter(
                    Q(id=parent_id) | Q(parent_id=parent_id)
                )
        
        # По умолчанию возвращаем только корневые сообщения (не ответы)
        return base_query.filter(parent__isnull=True)
    
    def get_serializer_class(self):
        """
        Выбираем сериализатор в зависимости от действия.
        """
        if self.action == 'list':
            return MessageListSerializer
        elif self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Переопределяем создание сообщения для обработки получателей и вложений.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Устанавливаем отправителя как текущего пользователя
        serializer.validated_data['sender'] = request.user
        
        # Сохраняем сообщение
        self.perform_create(serializer)
        
        # Возвращаем полные данные сообщения
        message = Message.objects.get(pk=serializer.instance.pk)
        response_serializer = MessageSerializer(message)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Отмечает сообщение как прочитанное для текущего пользователя.
        """
        message = self.get_object()
        
        try:
            recipient = MessageRecipient.objects.get(
                message=message,
                recipient=request.user
            )
            recipient.status = MessageStatus.READ
            recipient.read_at = timezone.now()
            recipient.save()
            return Response({"status": "marked as read"}, status=status.HTTP_200_OK)
        except MessageRecipient.DoesNotExist:
            return Response(
                {"error": "You are not a recipient of this message"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        """
        Отмечает сообщение звездочкой для текущего пользователя.
        """
        message = self.get_object()
        
        try:
            recipient = MessageRecipient.objects.get(
                message=message,
                recipient=request.user
            )
            recipient.is_starred = not recipient.is_starred  # Переключаем состояние
            recipient.save()
            return Response({"is_starred": recipient.is_starred}, status=status.HTTP_200_OK)
        except MessageRecipient.DoesNotExist:
            return Response(
                {"error": "You are not a recipient of this message"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def delete_for_me(self, request, pk=None):
        """
        Удаляет сообщение для текущего пользователя (не удаляет из базы).
        """
        message = self.get_object()
        
        try:
            recipient = MessageRecipient.objects.get(
                message=message,
                recipient=request.user
            )
            recipient.is_deleted = True
            recipient.save()
            return Response({"status": "deleted for you"}, status=status.HTTP_200_OK)
        except MessageRecipient.DoesNotExist:
            # Если пользователь отправитель, но не получатель
            if message.sender == request.user:
                # Помечаем сообщение как удаленное у отправителя (логика приложения)
                # Здесь можно добавить поле is_deleted_by_sender в модель Message
                # или обработать другим способом
                return Response({"status": "deleted for sender"}, status=status.HTTP_200_OK)
            return Response(
                {"error": "You are not related to this message"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class MessageAttachmentViewSet(viewsets.ModelViewSet):
    """
    API для работы с вложениями сообщений.
    """
    queryset = MessageAttachment.objects.all()
    serializer_class = MessageAttachmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Пользователь может видеть вложения только своих сообщений
        # и сообщений, в которых он является получателем
        return MessageAttachment.objects.filter(
            Q(message__sender=user) | 
            Q(message__recipients=user, message__message_recipients__is_deleted=False)
        ).distinct()

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    API для работы с объявлениями.
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsAnnouncementCreator]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_pinned', 'priority']
    search_fields = ['message__subject', 'message__content']
    ordering_fields = ['message__created_at', 'priority', 'expires_at']
    ordering = ['-is_pinned', '-priority', '-message__created_at']
    
    def get_queryset(self):
        """
        Возвращает объявления, доступные текущему пользователю.
        """
        user = self.request.user
        
        # Текущая дата для фильтрации по сроку действия
        now = timezone.now()
        
        # Базовый запрос для доступных объявлений
        base_query = Announcement.objects.filter(
            # Объявление активно (не истек срок)
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ).filter(
            # Пользователь имеет доступ к этому объявлению
            Q(message__sender=user) |  # Создатель объявления
            Q(message__recipients=user) |  # Прямой получатель
            Q(message__school__in=user.schools.all()) |  # Член учебного центра
            Q(message__branch__in=user.branches.all()) |  # Член филиала
            Q(message__group__in=user.groups.all())  # Член группы
        ).distinct()
        
        return base_query
    
    def perform_create(self, serializer):
        """
        При создании объявления автоматически устанавливаем отправителя.
        """
        message_data = serializer.validated_data.get('message_data', {})
        message_data['sender'] = self.request.user
        serializer.save()

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API для работы с уведомлениями.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsNotificationRecipient]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Возвращает уведомления для текущего пользователя.
        """
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Отмечает уведомление как прочитанное.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "marked as read"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Отмечает все непрочитанные уведомления как прочитанные.
        """
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({"status": "all marked as read"}, status=status.HTTP_200_OK)

class ChatGroupViewSet(viewsets.ModelViewSet):
    """
    API для работы с групповыми чатами.
    """
    serializer_class = ChatGroupSerializer
    permission_classes = [IsAuthenticated, IsChatGroupMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['school', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Возвращает чат-группы, в которых состоит текущий пользователь.
        """
        return ChatGroup.objects.filter(
            members=self.request.user
        ).annotate(
            unread_count=Count(
                Case(
                    When(
                        Q(message__message_type='group') & 
                        Q(message__message_recipients__recipient=self.request.user) & 
                        ~Q(message__message_recipients__status=MessageStatus.READ),
                        then=1
                    ),
                    output_field=IntegerField()
                )
            )
        )
    
    def perform_create(self, serializer):
        """
        При создании группы автоматически добавляем создателя в участники.
        """
        # Устанавливаем текущего пользователя как создателя
        serializer.save(created_by=self.request.user)
        
        # Добавляем создателя в список участников, если его там еще нет
        chat_group = serializer.instance
        chat_group.members.add(self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_members(self, request, pk=None):
        """
        Добавляет новых членов в группу чата.
        """
        chat_group = self.get_object()
        member_ids = request.data.get('member_ids', [])
        
        # Проверяем права доступа (только создатель или администратор)
        if chat_group.created_by != request.user:
            return Response(
                {"error": "Only the creator can add members"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Добавляем участников
        for member_id in member_ids:
            chat_group.members.add(member_id)
        
        return Response(
            {"status": f"Added {len(member_ids)} members"}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def remove_members(self, request, pk=None):
        """
        Удаляет членов из группы чата.
        """
        chat_group = self.get_object()
        member_ids = request.data.get('member_ids', [])
        
        # Проверяем права доступа
        if chat_group.created_by != request.user:
            return Response(
                {"error": "Only the creator can remove members"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Нельзя удалить создателя
        if str(chat_group.created_by.id) in member_ids or chat_group.created_by.id in member_ids:
            return Response(
                {"error": "Cannot remove the creator of the group"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Удаляем участников
        for member_id in member_ids:
            chat_group.members.remove(member_id)
        
        return Response(
            {"status": f"Removed {len(member_ids)} members"}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def leave_group(self, request, pk=None):
        """
        Позволяет пользователю выйти из группы.
        """
        chat_group = self.get_object()
        
        # Создатель не может выйти из группы, только удалить её
        if chat_group.created_by == request.user:
            return Response(
                {"error": "As the creator, you cannot leave the group, but you can delete it"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Удаляем пользователя из группы
        chat_group.members.remove(request.user)
        
        return Response({"status": "You have left the group"}, status=status.HTTP_200_OK)