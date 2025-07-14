from django import forms
from .models import Schedule
from courses.models import Group


class ScheduleForm(forms.ModelForm):
    # Create a multiple choice field for days of week
    DAYS_OF_WEEK = (
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    )
    
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        label='Дни недели',
        required=True
    )

    class Meta:
        model = Schedule
        fields = ['classroom', 'start_time', 'end_time', 'is_active']

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if not self.group:
            raise ValueError('Group must be provided')
            
        # Get selected days
        selected_days = self.cleaned_data['days_of_week']
        
        if not selected_days:
            raise forms.ValidationError('At least one day must be selected')
            
        # Create schedules for each selected day
        schedules = []
        for day in selected_days:
            schedule = Schedule(
                group=self.group,
                classroom=self.cleaned_data['classroom'],
                day_of_week=int(day),
                start_time=self.cleaned_data['start_time'],
                end_time=self.cleaned_data['end_time'],
                is_active=self.cleaned_data['is_active']
            )
            if commit:
                schedule.save()
            schedules.append(schedule)
        
        return schedules
    