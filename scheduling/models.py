# scheduling/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from courses.models import Group
from schools.models import Classroom
from datetime import timedelta, date, datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

class Schedule(models.Model):
    """
    Модель расписания занятий
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedules',
                           verbose_name=_('Группа'))
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True,
                               related_name='schedules', verbose_name=_('Аудитория'))
    day_of_week = models.IntegerField(_('День недели'), choices=(
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ))
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    is_active = models.BooleanField(_('Активное'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Расписание')
        verbose_name_plural = _('Расписания')
        ordering = ['day_of_week', 'start_time']
        unique_together = ('group', 'day_of_week', 'start_time')
    
    def __str__(self):
        return f"{self.group.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Проверка на перекрытие занятий в одной аудитории"""
        if self.classroom:
            overlapping = Schedule.objects.filter(
                classroom=self.classroom,
                day_of_week=self.day_of_week,
                is_active=True
            ).exclude(id=self.id)
            
            for other in overlapping:
                if (
                    (self.start_time <= other.start_time < self.end_time) or
                    (self.start_time < other.end_time <= self.end_time) or
                    (other.start_time <= self.start_time < other.end_time) or
                    (other.start_time < self.end_time <= other.end_time)
                ):
                    raise ValidationError(
                        f'Аудитория уже занята в это время: {other.group.name}'
                    )
    
    def create_lessons_for_period(self, start_date=None, end_date=None):
        """
        Создает уроки на основе расписания для указанного периода
        """
        if not start_date:
            start_date = date.today()
        
        if not end_date:
            # По умолчанию создаем на 2 месяца вперед
            end_date = start_date + timedelta(days=60)
        
        current_date = start_date
        created_lessons = []
        
        while current_date <= end_date:
            # Проверяем, соответствует ли день недели расписанию
            if current_date.weekday() == self.day_of_week:
                # Проверяем, нет ли уже урока на эту дату
                existing_lesson = Lesson.objects.filter(
                    schedule=self,
                    date=current_date
                ).first()
                
                if not existing_lesson:
                    lesson = Lesson.objects.create(
                        schedule=self,
                        date=current_date,
                        start_time=self.start_time,
                        end_time=self.end_time
                    )
                    created_lessons.append(lesson)
            
            current_date += timedelta(days=1)
        
        return created_lessons


class Lesson(models.Model):
    """Конкретное занятие на определенную дату"""
    
    schedule = models.ForeignKey(
        Schedule, 
        on_delete=models.CASCADE, 
        verbose_name='Расписание'
    )
    date = models.DateField('Дата занятия')
    
    # Время может отличаться от расписания (перенос)
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    
    # Содержание
    topic = models.CharField('Тема', max_length=200, blank=True)
    description = models.TextField('Описание', blank=True)
    homework = models.TextField('Домашнее задание', blank=True)
    
    # Статус
    is_conducted = models.BooleanField('Проведено', default=False)
    is_canceled = models.BooleanField('Отменено', default=False)
    cancel_reason = models.TextField('Причина отмены', blank=True)
    
    # Кто провел/отменил
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        verbose_name='Провел преподаватель'
    )
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['date', 'start_time']
        # Одно расписание - одно занятие в день
        unique_together = ('schedule', 'date')
    
    def __str__(self):
        status = ''
        if self.is_canceled:
            status = ' (отменено)'
        elif self.is_conducted:
            status = ' (проведено)'
        
        return f"{self.schedule.group.name} - {self.date} {self.start_time}{status}"
    
    def clean(self):
        """Проверки перед сохранением"""
        errors = {}
        
        # Время начала должно быть раньше времени окончания
        if self.start_time >= self.end_time:
            errors['end_time'] = 'Время окончания должно быть позже времени начала'
        
        # Дата должна соответствовать дню недели из расписания
        if self.date and self.date.weekday() != self.schedule.day_of_week:
            errors['date'] = f'Дата не соответствует дню недели из расписания ({self.schedule.get_day_of_week_display()})'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Если время не указано, берем из расписания
        if not self.start_time:
            self.start_time = self.schedule.start_time
        if not self.end_time:
            self.end_time = self.schedule.end_time
        
        super().save(*args, **kwargs)
    
    def mark_conducted(self, teacher):
        """Отметить занятие как проведенное"""
        self.is_conducted = True
        self.conducted_by = teacher
        self.save()
    
    def cancel(self, reason=''):
        """Отменить занятие"""
        self.is_canceled = True
        self.cancel_reason = reason
        self.save()


class Event(models.Model):
    """
    Модель события в календаре (не занятие, а другое событие)
    """
    title = models.CharField(_('Заголовок'), max_length=200)
    description = models.TextField(_('Описание'), blank=True)
    start_datetime = models.DateTimeField(_('Дата и время начала'))
    end_datetime = models.DateTimeField(_('Дата и время окончания'))
    location = models.CharField(_('Место проведения'), max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='created_events', verbose_name=_('Создано'))
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='events',
                                       verbose_name=_('Участники'), blank=True)
    is_public = models.BooleanField(_('Публичное'), default=False)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    class Meta:
        verbose_name = _('Событие')
        verbose_name_plural = _('События')
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.title} ({self.start_datetime.date()})"


# СИГНАЛЫ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ УРОКОВ

@receiver(post_save, sender=Schedule)
def auto_create_lessons(sender, instance, created, **kwargs):
    """
    Автоматически создает уроки при создании нового расписания
    или при активации существующего
    """
    # Создаем уроки только для активных расписаний
    if instance.is_active:
        # Если это новое расписание или расписание стало активным
        if created:
            print(f"Создание уроков для нового расписания: {instance}")
            lessons = instance.create_lessons_for_period()
            print(f"Создано {len(lessons)} уроков для группы {instance.group.name}")
        else:
            # Проверяем, есть ли будущие уроки
            future_lessons = Lesson.objects.filter(
                schedule=instance,
                date__gte=date.today()
            ).count()
            
            # Если будущих уроков меньше 10, создаем еще
            if future_lessons < 10:
                print(f"Дополнительное создание уроков для расписания: {instance}")
                lessons = instance.create_lessons_for_period()
                print(f"Создано {len(lessons)} дополнительных уроков")