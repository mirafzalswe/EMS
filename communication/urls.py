from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MessageViewSet, MessageAttachmentViewSet, 
    AnnouncementViewSet, NotificationViewSet, ChatGroupViewSet
)

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'attachments', MessageAttachmentViewSet, basename='attachment')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'chat-groups', ChatGroupViewSet, basename='chat-group')

urlpatterns = [
    path('', include(router.urls)),
]