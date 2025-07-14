from django.contrib import admin
from .models import (
    Message, MessageRecipient, MessageAttachment,
    Announcement, Notification, ChatGroup
)

class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient
    extra = 1
    readonly_fields = ('read_at',)

class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 1

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject', 'message_type', 'created_at', 'is_draft')
    list_filter = ('message_type', 'is_draft', 'school', 'branch')
    search_fields = ('subject', 'content', 'sender__username')
    date_hierarchy = 'created_at'
    inlines = [MessageRecipientInline, MessageAttachmentInline]
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = ('message', 'recipient', 'status', 'read_at', 'is_starred', 'is_deleted')
    list_filter = ('status', 'is_starred', 'is_deleted')
    search_fields = ('message__subject', 'recipient__username')
    date_hierarchy = 'read_at'
    readonly_fields = ('read_at',)

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('message', 'file_name', 'file_size', 'content_type', 'uploaded_at')
    list_filter = ('content_type',)
    search_fields = ('file_name', 'message__subject')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('file_size', 'uploaded_at')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('get_subject', 'expires_at', 'is_pinned', 'priority')
    list_filter = ('is_pinned',)
    search_fields = ('message__subject', 'message__content')
    date_hierarchy = 'expires_at'
    
    def get_subject(self, obj):
        return obj.message.subject if obj.message else '-'
    get_subject.short_description = 'Тема'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only for new announcements
            # Create a new message first
            message = Message.objects.create(
                sender=request.user,
                subject=form.cleaned_data.get('subject', ''),
                content=form.cleaned_data.get('content', ''),
                message_type='announcement'
            )
            obj.message = message
        super().save_model(request, obj, form, change)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('title', 'content', 'user__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'created_by', 'is_active', 'created_at')
    list_filter = ('school', 'is_active')
    search_fields = ('name', 'description', 'created_by__username')
    filter_horizontal = ('members',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
