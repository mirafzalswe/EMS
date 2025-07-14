from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Attendance, AttendanceStatus
from courses.models import Group
from scheduling.models import Lesson, Schedule
from users.models import User

@login_required
def mark_attendance(request, group_id):
    """
    View для отметки посещаемости группы.
    Показывает список студентов и позволяет отметить их присутствие.
    """
    # Проверяем права доступа
    if not (request.user.is_teacher or request.user.is_staff or request.user.is_admin):
        return HttpResponseForbidden("У вас нет прав для отметки посещаемости")

    # Получаем группу
    group = get_object_or_404(Group, id=group_id)
    
    # Получаем все даты занятий для этой группы
    # Берем только занятия на текущей неделе
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник текущей недели
    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье текущей недели
    
    available_dates = Lesson.objects.filter(
        schedule__group=group,
        date__range=[start_of_week, end_of_week]
    ).values_list('date', flat=True).distinct().order_by('-date')
    
    # Получаем выбранную дату из GET-параметров или используем текущую
    selected_date = request.GET.get('date')
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Получаем день недели для выбранной даты
    selected_weekday = selected_date.weekday()
    
    # Получаем все расписания группы на выбранный день недели
    schedules = Schedule.objects.filter(
        group=group,
        day_of_week=selected_weekday
    ).order_by('start_time')
    
    # Получаем выбранное расписание из GET-параметров
    selected_schedule_id = request.GET.get('schedule')
    selected_schedule = None
    
    if selected_schedule_id:
        try:
            selected_schedule = schedules.get(id=selected_schedule_id)
        except (Schedule.DoesNotExist, ValueError):
            selected_schedule = schedules.first()
    else:
        selected_schedule = schedules.first()

    # Если нет расписания, возвращаем шаблон с сообщением
    if not selected_schedule:
        context = {
            'group': group,
            'selected_date': selected_date,
            'schedules': schedules,
            'selected_schedule': None,
            'attendance_statuses': AttendanceStatus.choices,
            'available_dates': available_dates,
        }
        return render(request, 'attendance/mark_attendance.html', context)
    
    # Получаем или создаем занятие для выбранного расписания и даты
    current_lesson, created = Lesson.objects.get_or_create(
        schedule=selected_schedule,
        date=selected_date,
        defaults={
            'start_time': selected_schedule.start_time,
            'end_time': selected_schedule.end_time,
            'is_conducted': True
        }
    )

    # Получаем список студентов группы через enrollments
    students = User.objects.filter(
        enrollments__group=group,
        user_type='student',
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Получаем существующие отметки посещаемости
    attendance_dict = {}
    for attendance in Attendance.objects.filter(
        lesson=current_lesson,
        student__in=students
    ).select_related('student'):
        attendance_dict[attendance.student_id] = {
            'status': attendance.status,
            'comment': attendance.comment
        }

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            comment = request.POST.get(f'comment_{student.id}', '')
            
            if status:
                attendance, created = Attendance.objects.update_or_create(
                    student=student,
                    lesson=current_lesson,
                    defaults={
                        'status': status,
                        'comment': comment,
                        'marked_by': request.user,
                        'marked_at': timezone.now()
                    }
                )
        
        messages.success(request, 'Посещаемость успешно отмечена')
        return redirect('attendance:mark_attendance', group_id=group_id)

    context = {
        'group': group,
        'current_lesson': current_lesson,
        'students': students,
        'attendance_dict': attendance_dict,
        'attendance_statuses': AttendanceStatus.choices,
        'schedules': schedules,
        'selected_schedule': selected_schedule,
        'selected_date': selected_date,
        'available_dates': available_dates,
    }
    return render(request, 'attendance/mark_attendance.html', context)

@login_required
@require_POST
def update_attendance_status(request):
    """
    API endpoint для обновления статуса посещаемости через AJAX.
    """
    if not (request.user.is_teacher or request.user.is_staff or request.user.is_admin):
        return JsonResponse({'error': _('У вас нет прав для этой операции')}, status=403)
    
    student_id = request.POST.get('student_id')
    lesson_id = request.POST.get('lesson_id')
    status = request.POST.get('status')
    comment = request.POST.get('comment', '')
    
    if not all([student_id, lesson_id, status]):
        return JsonResponse({'error': _('Недостаточно данных')}, status=400)
    
    try:
        student = User.objects.get(id=student_id, user_type='student')
        lesson = Lesson.objects.get(id=lesson_id)
        
        # Проверяем, имеет ли пользователь доступ к этой группе
        if not (request.user.is_staff or request.user.is_admin or lesson.group.teacher == request.user):
            return JsonResponse({'error': _('У вас нет прав для этой операции')}, status=403)
        
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            lesson=lesson,
            defaults={
                'status': status,
                'comment': comment,
                'marked_by': request.user,
                'marked_at': timezone.now()
            }
        )
        
        return JsonResponse({
            'success': True,
            'status': attendance.get_status_display(),
            'status_class': status
        })
    
    except (User.DoesNotExist, Lesson.DoesNotExist):
        return JsonResponse({'error': _('Студент или занятие не найдены')}, status=404)

@login_required
def attendance_report(request, group_id):
    """
    View для просмотра отчета по посещаемости группы с расширенной статистикой.
    """
    group = get_object_or_404(Group, id=group_id)
    
    # Проверяем права доступа
    if not (request.user.is_teacher or request.user.is_staff or request.user.is_admin):
        messages.error(request, _("У вас нет прав для просмотра отчетов."))
        return redirect('group_detail', group_id=group_id)
    
    # Получаем параметры фильтрации
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Получаем все занятия группы
    lessons = Lesson.objects.filter(schedule__group=group)
    
    if start_date:
        lessons = lessons.filter(date__gte=start_date)
    if end_date:
        lessons = lessons.filter(date__lte=end_date)
    
    lessons = lessons.order_by('date', 'start_time')
    
    # Получаем студентов группы через enrollments
    students = User.objects.filter(
        enrollments__group=group,
        user_type='student',
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Создаем матрицу посещаемости с расчетом статистики
    attendance_matrix = []
    total_attendance = 0
    total_records = 0
    
    for student in students:
        student_attendance = {
            'student': student,
            'records': [],
            'present_count': 0,
            'total_lessons': 0
        }
        
        for lesson in lessons:
            attendance = Attendance.objects.filter(
                student=student,
                lesson=lesson
            ).first()
            
            student_attendance['records'].append({
                'lesson': lesson,
                'attendance': attendance
            })
            
            if attendance:
                student_attendance['total_lessons'] += 1
                if attendance.status in ['present', 'online']:
                    student_attendance['present_count'] += 1
                    total_attendance += 1
                total_records += 1
        
        # Рассчитываем процент посещаемости для студента
        if student_attendance['total_lessons'] > 0:
            student_attendance['attendance_rate'] = round(
                (student_attendance['present_count'] / student_attendance['total_lessons']) * 100
            )
        else:
            student_attendance['attendance_rate'] = 0
            
        attendance_matrix.append(student_attendance)
    
    # Рассчитываем общую статистику
    total_lessons = lessons.count()
    total_students = students.count()
    
    # Средний процент посещаемости
    attendance_rate = round((total_attendance / total_records * 100) if total_records > 0 else 0)
    
    context = {
        'group': group,
        'lessons': lessons,
        'attendance_matrix': attendance_matrix,
        'start_date': start_date,
        'end_date': end_date,
        'total_lessons': total_lessons,
        'total_students': total_students,
        'attendance_rate': attendance_rate,
    }
    
    return render(request, 'attendance/attendance_report.html', context)

@login_required
def student_attendance(request, student_id):
    """
    View для просмотра посещаемости конкретного студента.
    """
    student = get_object_or_404(User, id=student_id, user_type='student')
    
    # Проверяем права доступа
    if not (request.user.is_teacher or request.user.is_staff or request.user.is_admin or request.user == student):
        messages.error(request, _("У вас нет прав для просмотра этой информации."))
        return redirect('dashboard')
    
    # Получаем параметры фильтрации
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Получаем записи посещаемости
    attendance_records = Attendance.objects.filter(student=student)
    
    if start_date:
        
        attendance_records = attendance_records.filter(lesson__date__gte=start_date)
    if end_date:
        attendance_records = attendance_records.filter(lesson__date__lte=end_date)
    
    # Группируем по месяцам для статистики
    monthly_stats = {}
    for record in attendance_records:
        month = record.lesson.date.strftime('%Y-%m')
        if month not in monthly_stats:
            monthly_stats[month] = {
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
                'online': 0
            }
        
        monthly_stats[month]['total'] += 1
        monthly_stats[month][record.status] += 1
    
    context = {
        'student': student,
        'attendance_records': attendance_records,
        'monthly_stats': monthly_stats,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance/student_attendance.html', context)
