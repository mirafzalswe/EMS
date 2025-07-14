from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from courses.models import Group
from scheduling.models import Lesson

class AssignmentStatus(models.TextChoices):
    """Статусы задания"""
    DRAFT = 'draft', _('Draft')  # Черновик
    PUBLISHED = 'published', _('Published')  # Опубликовано
    Checked = 'Checked', _('Checked')  # Закрыто

class Assignment(models.Model):
    """
    Модель задания для группы
    """
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        verbose_name=_('Group')
    )
    due_date = models.DateTimeField(_('Due date'))
    max_points = models.PositiveIntegerField(_('Maximum points'), default=100)
    status = models.CharField(
        max_length=10,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.DRAFT,
        verbose_name=_('Status')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_assignments',
        verbose_name=_('Created by')
    )
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    attachment = models.FileField(
        _('Attachment'),
        upload_to='assignments/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Assignment')
        verbose_name_plural = _('Assignments')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.group.name}"

class Submission(models.Model):
    """
    Модель для отправленных работ студентов
    """
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Assignment')
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name=_('Student'),
        limit_choices_to={'user_type': 'student'}
    )
    content = models.TextField(_('Content'), blank=True)
    attachment = models.FileField(
        _('Attachment'),
        upload_to='submissions/',
        null=True,
        blank=True
    )
    points = models.PositiveIntegerField(_('Points'), null=True, blank=True)
    feedback = models.TextField(_('Feedback'), blank=True)
    submitted_at = models.DateTimeField(_('Submitted at'), default=timezone.now)
    graded_at = models.DateTimeField(_('Graded at'), null=True, blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions',
        verbose_name=_('Graded by')
    )

    class Meta:
        verbose_name = _('Submission')
        verbose_name_plural = _('Submissions')
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"
