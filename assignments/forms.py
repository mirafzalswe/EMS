from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Assignment, Submission, AssignmentStatus
from django.utils import timezone
import os
class AssignmentModelForm(forms.ModelForm):
    """
    Форма для создания и редактирования заданий
    """
    class Meta:
        model = Assignment
        fields = [
            'title',
            'description',
            'due_date',
            'max_points',
            'attachment',
            'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Название задания')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Описание задания')
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'max_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
 
        }

    def clean_due_date(self):
        """
        Проверка, что дата сдачи не в прошлом
        """
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError(
                _('Дата сдачи не может быть в прошлом')
            )
        return due_date

    def clean_max_points(self):
        """
        Проверка, что максимальный балл находится в допустимом диапазоне
        """
        max_points = self.cleaned_data.get('max_points')
        if max_points and (max_points < 0 or max_points > 100):
            raise forms.ValidationError(
                _('Максимальный балл должен быть от 0 до 100')
            )
        return max_points

class SubmissionForm(forms.ModelForm):
    """
    Форма для отправки решения задания
    """
    class Meta:
        model = Submission
        fields = ['attachment', 'content']
        widgets = {
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip,.rar'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Комментарий к решению (необязательно)')
            })
        }

    def clean_solution(self):
        """
        Проверка размера и типа файла
        """
        solution = self.cleaned_data.get('assigment')
        if solution:
            # Проверка размера файла (максимум 10MB)
            if solution.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    _('Размер файла не должен превышать 10MB')
                )
            
            # Проверка расширения файла
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
            ext = os.path.splitext(solution.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    _('Недопустимый формат файла. Разрешены: PDF, DOC, DOCX, TXT, ZIP, RAR')
                )
        return solution

# class GradeSubmissionForm(forms.ModelForm):
#     """
#     Форма для оценки решения задания
#     """
#     class Meta:
#         model = Submission
#         fields = ['grade', 'feedback']
#         widgets = {
#             'grade': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'min': 0,
#                 'max': 100,
#                 'step': 0.1
#             }),
#             'feedback': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 4,
#                 'placeholder': _('Комментарий к оценке')
#             })
#         }

#     def clean_grade(self):
#         """
#         Проверка, что оценка находится в допустимом диапазоне
#         """
#         grade = self.cleaned_data.get('grade')
#         if grade is not None:
#             if grade < 0 or grade > 100:
#                 raise forms.ValidationError(
#                     _('Оценка должна быть от 0 до 100')
#                 )
#         return grade

# class AssignmentFilterForm(forms.Form):
#     """
#     Форма для фильтрации списка заданий
#     """
#     STATUS_CHOICES = [
#         ('', _('Все статусы')),
#         ('published', _('Опубликованные')),
#         ('draft', _('Черновики')),
#         ('expired', _('Просроченные'))
#     ]

#     status = forms.ChoiceField(
#         choices=STATUS_CHOICES,
#         required=False,
#         widget=forms.Select(attrs={
#             'class': 'form-control'
#         })
#     )
    
#     search = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': _('Поиск по названию')
#         })
#     )

#     def clean(self):
#         """
#         Дополнительная валидация формы фильтрации
#         """
#         cleaned_data = super().clean()
#         status = cleaned_data.get('status')
#         search = cleaned_data.get('search')

#         if not status and not search:
#             raise forms.ValidationError(
#                 _('Пожалуйста, укажите хотя бы один параметр фильтрации')
#             )

#         return cleaned_data