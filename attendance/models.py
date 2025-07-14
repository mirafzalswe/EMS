# attendance/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from courses.models import Group, Course, Enrollment
from scheduling.models import Lesson

class AttendanceStatus(models.TextChoices):
    """Статусы посещения занятия"""
    PRESENT = 'present', _('Present')  # Присутствует
    ABSENT = 'absent', _('Absent')  # Отсутствует
    LATE = 'late', _('Late')  # Опоздал
    EXCUSED = 'excused', _('Excused absence')  # Уважительная причина
    ONLINE = 'online', _('Attended online')  # Присутствовал онлайн

class Attendance(models.Model):
    """
    Модель для отслеживания посещаемости студентов на занятиях.
    Каждая запись представляет посещение (или пропуск) конкретного студента на конкретном занятии.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name=_('Student'),
        limit_choices_to={'user_type': 'student'}
    )
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name=_('Lesson')
    )
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
        verbose_name=_('Attendance status')
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='marked_attendances',
        verbose_name=_('Marked by')
    )
    marked_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Marked at')
    )
    comment = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Comment')
    )
    
    class Meta:
        verbose_name = _('Attendance record')
        verbose_name_plural = _('Attendance records')
        # Уникальное ограничение: один студент может иметь только одну запись посещаемости для конкретного занятия
        unique_together = ('student', 'lesson')
        ordering = ['-lesson__date', '-lesson__start_time']
    
    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.get_status_display()}"

class AttendanceReport(models.Model):
    """
    Модель для сохранения сгенерированных отчетов о посещаемости.
    Позволяет сохранять параметры отчета и его результаты для последующего использования.
    """
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='attendance_reports',
        verbose_name=_('Group')
    )
    start_date = models.DateField(verbose_name=_('Start date'))
    end_date = models.DateField(verbose_name=_('End date'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_attendance_reports',
        verbose_name=_('Created by')
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Created at')
    )
    report_data = models.JSONField(
        verbose_name=_('Report data'),
        help_text=_('JSON data with report results')
    )
    
    class Meta:
        verbose_name = _('Attendance report')
        verbose_name_plural = _('Attendance reports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Attendance report for {self.group} ({self.start_date} - {self.end_date})"