from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Lead, LeadSource, Section, GroupSchedule, TempLead
from courses.models import Course, Group
from users.models import User

class LeadForm(forms.ModelForm):
    """Форма для создания и редактирования лидов"""
    class Meta:
        model = Lead
        fields = ['first_name', 'last_name', 'phone', 'email', 'gender', 
                 'source', 'section', 'interested_course', 'notes']
        widgets = {
            'gender': forms.Select(attrs={'class': 'select form-select'}),
            'source': forms.Select(attrs={'class': 'select form-select'}),
            'section': forms.Select(attrs={
                'class': 'select form-select',
                'data-placeholder': 'Выберите раздел'
            }),
            'interested_course': forms.Select(attrs={'class': 'select form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем пустой вариант для раздела
        self.fields['section'].empty_label = "Выберите раздел"
        # Группируем разделы по колонкам для удобства выбора
        sections = Section.objects.all().order_by('column', 'order')
        choices = [('', self.fields['section'].empty_label)]
        
        column_names = {
            'new': 'Новые студенты',
            'waiting': 'В режиме ожидания',
            'trial': 'На пробном уроке',
            'attending': 'Посещают занятия'
        }
        
        current_column = None
        group_choices = []
        
        for section in sections:
            if current_column != section.column:
                if group_choices:
                    choices.append((column_names.get(current_column, current_column), group_choices))
                current_column = section.column
                group_choices = []
            group_choices.append((section.id, section.name))
            
        if group_choices:
            choices.append((column_names.get(current_column, current_column), group_choices))
            
        self.fields['section'].choices = choices

class LeadFilterForm(forms.Form):
    """Форма для фильтрации лидов на доске"""
    source = forms.ModelChoiceField(
        queryset=LeadSource.objects.filter(is_active=True),
        required=False,
        empty_label="Barcha manbalar",
        widget=forms.Select(attrs={'class': 'select form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Izlash...', 'class': 'form-control'})
    )

class SectionForm(forms.ModelForm):
    """Форма для создания разделов в колонках"""
    class Meta:
        model = Section
        fields = ['name', 'column']
        widgets = {
            'column': forms.Select(attrs={'class': 'select form-select'}),
        }

class GroupAssignmentForm(forms.Form):
    """Форма для назначения лида в группу"""
    group = forms.ModelChoiceField(
        queryset=Group.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'select form-select'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False
    )

class NewGroupForm(forms.ModelForm):
    """Форма для создания новой группы"""
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='teacher', is_active=True),
        label=_('Преподаватель'),
        widget=forms.Select(attrs={'class': 'select form-select'})
    )
    
    schedule_type = forms.ChoiceField(
        choices=(
            ('odd', _('Нечетные дни')),
            ('even', _('Четные дни')),
            ('weekend', _('Выходные дни')),
            ('daily', _('Ежедневно')),
            ('other', _('Другое')),
        ),
        label=_('Тип расписания'),
        widget=forms.Select(attrs={'class': 'select form-select'})
    )
    
    start_time = forms.TimeField(
        label=_('Время начала'),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'min': '07:00', 'max': '21:00'})
    )
    
    end_time = forms.TimeField(
        label=_('Время окончания'),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'min': '07:30', 'max': '21:30'})
    )
    
    class Meta:
        model = Group
        fields = ['name', 'course', 'branch', 'max_students']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'select form-select'}),
            'branch': forms.Select(attrs={'class': 'select form-select'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30'}),
        }

class LeadNoteForm(forms.Form):
    """Форма для добавления заметки к лиду"""
    note = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label=_('Заметка')
    )

class TempLeadForm(forms.ModelForm):
    """Форма для создания временных студентов"""
    class Meta:
        model = TempLead
        fields = ['first_name', 'last_name', 'phone', 'email', 'gender', 
                 'source', 'section', 'interested_course', 'notes']
        widgets = {
            'gender': forms.Select(attrs={'class': 'select form-select'}),
            'source': forms.Select(attrs={'class': 'select form-select'}),
            'section': forms.Select(attrs={
                'class': 'select form-select',
                'data-placeholder': 'Выберите раздел'
            }),
            'interested_course': forms.Select(attrs={'class': 'select form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем пустой вариант для раздела
        self.fields['section'].empty_label = "Выберите раздел"
        # Группируем разделы по колонкам для удобства выбора
        sections = Section.objects.all().order_by('column', 'order')
        choices = [('', self.fields['section'].empty_label)]
        
        column_names = {
            'new': 'Новые студенты',
            'waiting': 'В режиме ожидания',
            'trial': 'На пробном уроке',
            'attending': 'Посещают занятия'
        }
        
        current_column = None
        group_choices = []
        
        for section in sections:
            if current_column != section.column:
                if group_choices:
                    choices.append((column_names.get(current_column, current_column), group_choices))
                current_column = section.column
                group_choices = []
            group_choices.append((section.id, section.name))
            
        if group_choices:
            choices.append((column_names.get(current_column, current_column), group_choices))
            
        self.fields['section'].choices = choices