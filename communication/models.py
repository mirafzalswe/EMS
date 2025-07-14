from django.db import models
from django.conf import settings
from schools.models import School, Branch
from courses.models import Group, Course
from users.models import User

class MessageType(models.TextChoices):
    """
    Типы сообщений в системе коммуникации.
    """
    PRIVATE = 'private', 'Личное сообщение'
    GROUP = 'group', 'Групповое сообщение'
    ANNOUNCEMENT = 'announcement', 'Объявление'
    NOTIFICATION = 'notification', 'Уведомление'

class MessageStatus(models.TextChoices):
    """
    Статусы сообщений для отслеживания прочтения.
    """
    SENT = 'sent', 'Отправлено'
    DELIVERED = 'delivered', 'Доставлено'
    READ = 'read', 'Прочитано'

class Message(models.Model):
    """
    Модель для хранения всех типов сообщений в системе.
    """
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        through='MessageRecipient',
        related_name='received_messages',
        verbose_name='Получатели'
    )
    subject = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name='Тема'
    )
    content = models.TextField(verbose_name='Содержание')
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.PRIVATE,
        verbose_name='Тип сообщения'
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='Группа'
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='Учебный центр'
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name='Филиал'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_draft = models.BooleanField(default=False, verbose_name='Черновик')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='replies',
        verbose_name='Родительское сообщение'
    )
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_message_type_display()} от {self.sender}: {self.subject}"

class MessageRecipient(models.Model):
    """
    Промежуточная модель для связи сообщений с получателями и 
    хранения статуса прочтения для каждого получателя.
    """
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE,
        related_name='message_recipients',
        verbose_name='Сообщение'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='message_statuses',
        verbose_name='Получатель'
    )
    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.SENT,
        verbose_name='Статус'
    )
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Время прочтения')
    is_starred = models.BooleanField(default=False, verbose_name='Отмечено звездой')
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено у получателя')
    
    class Meta:
        verbose_name = 'Статус сообщения'
        verbose_name_plural = 'Статусы сообщений'
        unique_together = ['message', 'recipient']
        
    def __str__(self):
        return f"Сообщение {self.message.id} для {self.recipient}"

class MessageAttachment(models.Model):
    """
    Модель для хранения файлов, прикрепленных к сообщениям.
    """
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Сообщение'
    )
    file = models.FileField(upload_to='message_attachments/', verbose_name='Файл')
    file_name = models.CharField(max_length=255, verbose_name='Имя файла')
    file_size = models.IntegerField(verbose_name='Размер файла (байт)')
    content_type = models.CharField(max_length=100, verbose_name='Тип содержимого')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    
    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        
    def __str__(self):
        return self.file_name

class Announcement(models.Model):
    """
    Модель для объявлений с расширенными возможностями.
    Наследуется от Message через OneToOne связь.
    """
    message = models.OneToOneField(
        Message, 
        on_delete=models.CASCADE,
        related_name='announcement_details',
        verbose_name='Сообщение'
    )
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Действует до')
    is_pinned = models.BooleanField(default=False, verbose_name='Закреплено')
    priority = models.IntegerField(default=0, verbose_name='Приоритет')
    
    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        
    def __str__(self):
        return f"Объявление: {self.message.subject}"

class Notification(models.Model):
    """
    Системные уведомления для пользователей.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    link = models.URLField(blank=True, null=True, verbose_name='Ссылка')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Уведомление для {self.user}: {self.title}"

class ChatGroup(models.Model):
    """
    Модель для групповых чатов, отдельных от учебных групп.
    """
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_groups',
        verbose_name='Участники'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_chat_groups',
        verbose_name='Создатель'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='chat_groups',
        verbose_name='Учебный центр'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Чат-группа'
        verbose_name_plural = 'Чат-группы'
        
    def __str__(self):
        return self.name