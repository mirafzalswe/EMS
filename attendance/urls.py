# attendance/urls.py
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Маркировка посещаемости
    path('group/<int:group_id>/mark/', views.mark_attendance, name='mark_attendance'),
    
    # API для обновления статуса посещаемости
    path('update-status/', views.update_attendance_status, name='update_attendance_status'),
    
    # # Отчет по посещаемости группы
    path('group/<int:group_id>/report/', views.attendance_report, name='attendance_report'),
    
    # # История посещаемости студента
    path('student/<int:student_id>/', views.student_attendance, name='student_attendance'),
]