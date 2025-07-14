from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from courses.models import Group, Enrollment
from .models import Assignment, Submission, AssignmentStatus
from .forms import AssignmentModelForm, SubmissionForm
from users.permissions import IsTeacherOrAdmin

@login_required
def create_assignment(request, group_id):
    """
    View для создания нового задания для группы
    """
    group = get_object_or_404(Group, id=group_id)
    
    # Проверяем права доступа
    if request.user != group.teacher and not request.user.is_staff and not request.user.is_admin:
        messages.error(request, 'У вас нет прав для создания заданий')
        return redirect('group-detail', group_id=group.id)

    if request.method == 'POST':
        form = AssignmentModelForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.group = group
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, 'Задание успешно создано!')
            return redirect('assignment_list', group_id=group_id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = AssignmentModelForm()

    context = {
        'form': form,
        'group': group
    }
    return render(request, 'assignments/create_assignment.html', context)

@login_required
def assignment_list(request, group_id):
    """
    View для отображения списка заданий группы
    """
    group = get_object_or_404(Group, id=group_id)
    
    # Проверяем, является ли пользователь студентом группы или преподавателем
    is_student = Enrollment.objects.filter(
        group=group,
        student=request.user,
        is_active=True
    ).exists()
    
    if not (is_student or request.user == group.teacher or request.user.is_staff or request.user.is_admin):
        messages.error(request, 'У вас нет доступа к этой группе')
        return redirect('dashboard')

    assignments = Assignment.objects.filter(group=group).order_by('-created_at')
    
    context = {
        'group': group,
        'assignments': assignments,
        'is_teacher': request.user == group.teacher or request.user.is_staff or request.user.is_admin
    }
    return render(request, 'assignments/assignment_list.html', context)

@login_required
def assignment_detail(request, assignment_id):
    """
    View для просмотра деталей задания
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    group = assignment.group
    students = Enrollment.objects.filter(group=group, is_active=True).select_related('student')
    submissions = Submission.objects.filter(assignment=assignment, student__in=students.values_list('student', flat=True))

    # Добавляем статус оценки для каждого submission
    for submission in submissions:
        if submission.points is not None:
            max_points = assignment.max_points
            grade_percentage = (submission.points / max_points) * 100
            if grade_percentage >= 60:
                submission.grade_status = 'success'
            elif grade_percentage >= 40:
                submission.grade_status = 'warning'
            else:
                submission.grade_status = 'danger'
        else:
            submission.grade_status = None

    # Проверяем права доступа
    is_student = Enrollment.objects.filter(
        group=group,
        student=request.user,
        is_active=True
    ).exists()
    
    if not (is_student or request.user == group.teacher or request.user.is_staff or request.user.is_admin):
        messages.error(request, 'У вас нет доступа к этому заданию')
        return redirect('assignment_detail', assignment_id=assignment.id)

    # Обработка оценки работы
    if request.method == 'POST' and (request.user == group.teacher or request.user.is_staff or request.user.is_admin):
        submission_id = request.POST.get('submission_id')
        points = request.POST.get('grade')  # Используем grade из формы как points
        feedback = request.POST.get('feedback', '')
        
        try:
            submission = Submission.objects.get(id=submission_id, assignment=assignment)
            submission.points = points
            submission.feedback = feedback
            submission.graded_by = request.user
            submission.graded_at = timezone.now()
            submission.save()
            messages.success(request, 'Оценка успешно сохранена!')
        except Submission.DoesNotExist:
            messages.error(request, 'Работа не найдена')
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении оценки: {str(e)}')
        
        return redirect('assignment_detail', assignment_id=assignment.id)

    # Получаем submission студента, если он студент
    submission = None
    if request.user.user_type == 'student':
        submission = Submission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()
        
        # Вычисляем grade_status для submission студента
        if submission and submission.points is not None:
            max_points = assignment.max_points
            grade_percentage = (submission.points / max_points) * 100
            if grade_percentage >= 60:
                submission.grade_status = 'success'
            elif grade_percentage >= 40:
                submission.grade_status = 'warning'
            else:
                submission.grade_status = 'danger'
        elif submission:
            submission.grade_status = None

    context = {
        'students_submissions': submissions,
        'assignment': assignment,
        'submission': submission,
        'is_teacher': request.user == group.teacher or request.user.is_staff or request.user.is_admin
    }
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """
    View для отправки решения задания
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Проверяем, является ли пользователь студентом группы
    if not Enrollment.objects.filter(
        group=assignment.group,
        student=request.user,
        is_active=True
    ).exists():
        messages.error(request, 'У вас нет прав для отправки этого задания')
        return redirect('dashboard')

    # Проверяем дедлайн
    if timezone.now() > assignment.due_date:
        messages.error(request, 'Срок сдачи задания истек')
        return redirect('assignment_detail', assignment_id=assignment.id)

    # Получаем существующее решение, если оно есть
    submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()
            
            if submission:
                messages.success(request, 'Решение успешно обновлено!')
            else:
                messages.success(request, 'Решение успешно отправлено!')
                
            return redirect('assignment_detail', assignment_id=assignment.id)
    else:
        form = SubmissionForm(instance=submission)

    context = {
        'form': form,
        'assignment': assignment,
        'submission': submission
    }
    return render(request, 'assignments/submit_assignment.html', context)
