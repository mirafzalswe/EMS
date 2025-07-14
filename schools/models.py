# schools/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class School(models.Model):
    """
    Модель учебного центра
    """
    name = models.CharField(_('Название'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    address = models.CharField(_('Адрес'), max_length=255, blank=True)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    website = models.URLField(_('Веб-сайт'), blank=True)
    logo = models.ImageField(_('Логотип'), upload_to='schools/logos/', null=True, blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Учебный центр')
        verbose_name_plural = _('Учебные центры')

    def __str__(self):
        return self.name


class Branch(models.Model):
    """
    Модель филиала учебного центра
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='branches',
                               verbose_name=_('Учебный центр'))
    name = models.CharField(_('Название'), max_length=200)
    address = models.CharField(_('Адрес'), max_length=255)
    phone = models.CharField(_('Телефон'), max_length=20, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='managed_branches',
                                verbose_name=_('Управляющий'),
                                limit_choices_to={'user_type': 'admin'})

    class Meta:
        verbose_name = _('Филиал')
        verbose_name_plural = _('Филиалы')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Classroom(models.Model):
    """
    Модель учебной аудитории
    """
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='classrooms',
                               verbose_name=_('Филиал'))
    name = models.CharField(_('Название'), max_length=100)
    capacity = models.PositiveIntegerField(_('Вместимость'), default=1)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активный'), default=True)

    class Meta:
        verbose_name = _('Аудитория')
        verbose_name_plural = _('Аудитории')

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class SchoolStaffAssignment(models.Model):
    """
    Назначение сотрудников в учебные центры
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='staff_assignments',
                               verbose_name=_('Учебный центр'))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='school_assignments',
                             verbose_name=_('Пользователь'))
    position = models.CharField(_('Должность'), max_length=100, blank=True)
    start_date = models.DateField(_('Дата начала работы'))
    end_date = models.DateField(_('Дата окончания работы'), null=True, blank=True)
    is_active = models.BooleanField(_('Активный'), default=True)

    class Meta:
        verbose_name = _('Назначение сотрудника')
        verbose_name_plural = _('Назначения сотрудников')
        unique_together = ('school', 'user', 'start_date')

    def __str__(self):
        return f"{self.user} - {self.school} ({self.position})"