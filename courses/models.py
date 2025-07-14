# courses/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from schools.models import School, Branch
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta


class Subject(models.Model):
    """
    Модель предмета/дисциплины
    """
    name = models.CharField(_('Название'), max_length=100)
    description = models.TextField(_('Описание'), blank=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects',
                               verbose_name=_('Учебный центр'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Предмет')
        verbose_name_plural = _('Предметы')
        unique_together = ('name', 'school')

    def __str__(self):
        return f"{self.name} ({self.school.name})"


class Course(models.Model):
    """
    Модель курса обучения
    """
    name = models.CharField(_('Название'), max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses',
                                verbose_name=_('Предмет'))
    description = models.TextField(_('Описание'), blank=True)
    price = models.DecimalField(_('Стоимость'), max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(_('Продолжительность (часов)'))
    duration_type = models.CharField(_('Тип продолжительности'), max_length=20,
                                     choices=(
                                         ('hours', 'Часы'),
                                         ('days', 'Дни'),
                                         ('weeks', 'Недели'),
                                         ('months', 'Месяцы'),
                                     ), default='hours')
    available_branches = models.ManyToManyField(Branch, related_name='available_courses',
                                                verbose_name=_('Доступные филиалы'))
    is_active = models.BooleanField(_('Активный'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Курс')
        verbose_name_plural = _('Курсы')

    def __str__(self):
        return f"{self.name} ({self.subject.name})"


class Group(models.Model):
    """
    Модель учебной группы
    """
    name = models.CharField(_('Название'), max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups',
                               verbose_name=_('Курс'))
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='groups',
                               verbose_name=_('Филиал'))
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='teaching_groups', verbose_name=_('Преподаватель'),
                                limit_choices_to={'user_type': 'teacher'})
    max_students = models.PositiveIntegerField(_('Максимальное количество учеников'), default=15)
    is_active = models.BooleanField(_('Активная'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)

    class Meta:
        verbose_name = _('Группа')
        verbose_name_plural = _('Группы')

    def __str__(self):
        return f"{self.name} ({self.course.name})"

    @property
    def students_count(self):
        """Количество студентов в группе"""
        return self.enrollments.count()

    @property
    def is_full(self):
        """Проверка, заполнена ли группа"""
        return self.students_count >= self.max_students


class Enrollment(models.Model):
    """
    Модель зачисления студента в группу
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='enrollments', verbose_name=_('Студент'),
                                limit_choices_to={'user_type': 'student'})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='enrollments',
                              verbose_name=_('Группа'))
    enrollment_date = models.DateField(_('Дата зачисления'), auto_now_add=True)
    is_active = models.BooleanField(_('Активный'), default=True)
    notes = models.TextField(_('Примечания'), blank=True)

    class Meta:
        verbose_name = _('Зачисление')
        verbose_name_plural = _('Зачисления')
        unique_together = ('student', 'group')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.name}"


class LearningMaterial(models.Model):
    """
    Модель учебных материалов
    """
    title = models.CharField(_('Заголовок'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials',
                               verbose_name=_('Курс'))
    file = models.FileField(_('Файл'), upload_to='learning_materials/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='uploaded_materials',
                                   verbose_name=_('Создано'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('Учебный материал')
        verbose_name_plural = _('Учебные материалы')

    def __str__(self):
        return self.title


@receiver(post_save, sender=Enrollment)
def create_future_payments_on_enrollment(sender, instance, created, **kwargs):
    if created:
        from finance.models import FuturePayment  # ленивый импорт для избежания циклического импорта
        student = instance.student
        group = instance.group
        course = group.course
        price = course.price
        start_date = instance.enrollment_date
        # Создаём оплаты на 3 месяца вперёд
        for i in range(3):
            pay_date = (start_date.replace(day=1) + timedelta(days=32*i)).replace(day=start_date.day)
            if not FuturePayment.objects.filter(student=student, group=group, payment_date=pay_date).exists():
                FuturePayment.objects.create(
                    student=student,
                    group=group,
                    payment_date=pay_date,
                    amount=price,
                    status="pending"
                )