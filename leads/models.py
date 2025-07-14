from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from courses.models import Course, Group

class LeadSource(models.Model):
    """Источники лидов (Instagram, Telegram, и т.д.)"""
    name = models.CharField(_('Название'), max_length=50)
    description = models.TextField(_('Описание'), blank=True)
    is_active = models.BooleanField(_('Активный'), default=True)
    
    class Meta:
        verbose_name = _('Источник лидов')
        verbose_name_plural = _('Источники лидов')
        
    def __str__(self):
        return self.name

class LeadStatus(models.Model):
    """Статусы лидов (Новый, В ожидании, и т.д.)"""
    name = models.CharField(_('Название'), max_length=50)
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    
    class Meta:
        verbose_name = _('Статус лида')
        verbose_name_plural = _('Статусы лидов')
        ordering = ['order']
        
    def __str__(self):
        return self.name

class Lead(models.Model):
    """Модель лида/потенциального студента"""
    GENDER_CHOICES = (
        ('male', _('Мужской')),
        ('female', _('Женский')),
    )
    
    first_name = models.CharField(_('Имя'), max_length=100)
    last_name = models.CharField(_('Фамилия'), max_length=100)
    phone = models.CharField(_('Телефон'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    gender = models.CharField(_('Пол'), max_length=10, choices=GENDER_CHOICES, blank=True)
    
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, 
                             related_name='leads', verbose_name=_('Источник'),
                             null=True, blank=True)
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL,
                             related_name='leads', verbose_name=_('Статус'),
                             null=True)
    
    # Связь с разделом
    section = models.ForeignKey('Section', on_delete=models.SET_NULL,
                              related_name='leads', verbose_name=_('Раздел'),
                              null=True, blank=True)
    
    notes = models.TextField(_('Примечания'), blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    
    # Если лид конвертирован в студента
    converted_to_student = models.BooleanField(_('Конвертирован в студента'), default=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              related_name='lead_record', verbose_name=_('Студент'),
                              null=True, blank=True,
                              limit_choices_to={'user_type': 'student'})
    
    # Курс, которым интересуется
    interested_course = models.ForeignKey(Course, on_delete=models.SET_NULL,
                                       related_name='interested_leads', 
                                       verbose_name=_('Интересующий курс'),
                                       null=True, blank=True)
    
    # Поля для системы Канбан
    board_column = models.CharField(_('Колонка на доске'), max_length=50, default='new',
                                choices=(
                                    ('new', _('Новые студенты')),
                                    ('waiting', _('В режиме ожидания')),
                                    ('trial', _('На пробном уроке')),
                                    ('attending', _('Посещают занятия')),
                                ))
    
    order_in_column = models.PositiveIntegerField(_('Порядок в колонке'), default=0)
    
    class Meta:
        verbose_name = _('Лид')
        verbose_name_plural = _('Лиды')
        ordering = ['board_column', 'order_in_column']
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
    
    def convert_to_student(self, user):
        """Конвертировать лид в студента"""
        self.converted_to_student = True
        self.student = user
        self.save()

class Section(models.Model):
    """Разделы внутри колонок на доске (опционально)"""
    name = models.CharField(_('Название'), max_length=100)
    column = models.CharField(_('Колонка'), max_length=50,
                           choices=(
                               ('new', _('Новые студенты')),
                               ('waiting', _('В режиме ожидания')),
                               ('trial', _('На пробном уроке')),
                               ('attending', _('Посещают занятия')),
                           ))
    order = models.PositiveSmallIntegerField(_('Порядок'), default=0)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Раздел')
        verbose_name_plural = _('Разделы')
        ordering = ['column', 'order']
        
    def __str__(self):
        return f"{self.name} ({self.get_column_display()})"

class LeadActivity(models.Model):
    """История активности по лиду"""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, 
                          related_name='activities', verbose_name=_('Лид'))
    activity_type = models.CharField(_('Тип активности'), max_length=50, 
                                 choices=(
                                     ('status_change', _('Изменение статуса')),
                                     ('note_added', _('Добавление заметки')),
                                     ('group_assignment', _('Назначение в группу')),
                                     ('contact', _('Контакт')),
                                 ))
    description = models.TextField(_('Описание'))
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  related_name='lead_activities', 
                                  verbose_name=_('Выполнено'),
                                  null=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Активность лида')
        verbose_name_plural = _('Активности лидов')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead}"

class ScheduleType(models.Model):
    """Типы расписания для групп"""
    name = models.CharField(_('Название'), max_length=50)
    description = models.TextField(_('Описание'), blank=True)
    
    class Meta:
        verbose_name = _('Тип расписания')
        verbose_name_plural = _('Типы расписания')
        
    def __str__(self):
        return self.name

class GroupSchedule(models.Model):
    """Расписание для групп"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, 
                           related_name='lead_schedules', verbose_name=_('Группа'))
    schedule_type = models.ForeignKey(ScheduleType, on_delete=models.CASCADE,
                                    related_name='group_schedules', 
                                    verbose_name=_('Тип расписания'))
    start_time = models.TimeField(_('Время начала'))
    end_time = models.TimeField(_('Время окончания'))
    
    class Meta:
        verbose_name = _('Расписание группы')
        verbose_name_plural = _('Расписания групп')
        
    def __str__(self):
        return f"{self.group.name} - {self.schedule_type.name} ({self.start_time}-{self.end_time})"

class TempLead(models.Model):
    """Модель для временных студентов"""
    GENDER_CHOICES = (
        ('male', _('Мужской')),
        ('female', _('Женский')),
    )
    
    first_name = models.CharField(_('Имя'), max_length=100)
    last_name = models.CharField(_('Фамилия'), max_length=100)
    phone = models.CharField(_('Телефон'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    gender = models.CharField(_('Пол'), max_length=10, choices=GENDER_CHOICES, blank=True)
    
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, 
                             related_name='temp_leads', verbose_name=_('Источник'),
                             null=True, blank=True)
    
    section = models.ForeignKey(Section, on_delete=models.SET_NULL,
                              related_name='temp_leads', verbose_name=_('Раздел'),
                              null=True, blank=True)
    
    interested_course = models.ForeignKey(Course, on_delete=models.SET_NULL,
                                       related_name='interested_temp_leads', 
                                       verbose_name=_('Интересующий курс'),
                                       null=True, blank=True)
    
    notes = models.TextField(_('Примечания'), blank=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_processed = models.BooleanField(_('Обработан'), default=False)
    
    class Meta:
        verbose_name = _('Временный студент')
        verbose_name_plural = _('Временные студенты')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"
    
    def convert_to_lead(self):
        """Конвертировать временного студента в лид"""
        lead = Lead.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            phone=self.phone,
            email=self.email,
            gender=self.gender,
            source=self.source,
            section=self.section,
            interested_course=self.interested_course,
            notes=self.notes,
            board_column=self.section.column if self.section else 'new'
        )
        self.is_processed = True
        self.save()
        return lead