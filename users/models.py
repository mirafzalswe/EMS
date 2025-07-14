# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Кастомная модель пользователя с дополнительными полями
    """
    USER_TYPE_CHOICES = (
        ('admin', 'Администратор'),
        ('teacher', 'Преподаватель'),
        ('student', 'Ученик'),
        ('parent', 'Родитель'),
        ('methodist', 'Методист'),
    )

    user_type = models.CharField(_('Тип пользователя'), max_length=20, choices=USER_TYPE_CHOICES)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    birthday = models.DateField(_('Дата рождения'), null=True, blank=True)
    avatar = models.ImageField(_('Аватар'), upload_to='teacher_photos/', null=True, blank=True, default="teacher_photos/default.png")
    bio = models.TextField(_('О себе'), blank=True)

    # Дополнительные поля для преподавателей
    specialization = models.CharField(_('Специализация'), max_length=100, blank=True)
    experience = models.PositiveIntegerField(_('Опыт работы (лет)'), null=True, blank=True)

    # Дополнительные поля для учеников
    parent = models.ForeignKey('self', verbose_name=_('Родитель'),
                               on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='children', limit_choices_to={'user_type': 'parent'})

    # Настройки уведомлений
    email_notifications = models.BooleanField(_('Email-уведомления'), default=True)
    sms_notifications = models.BooleanField(_('SMS-уведомления'), default=False)

    # Override groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    @property
    def is_admin(self):
        return self.user_type == 'admin'

    @property
    def is_teacher(self):
        return self.user_type == 'teacher'

    @property
    def is_student(self):
        return self.user_type == 'student'

    @property
    def is_parent(self):
        return self.user_type == 'parent'

    @property
    def is_methodist(self):
        return self.user_type == 'methodist'