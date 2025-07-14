# courses/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Subject, Course, Group, Enrollment, LearningMaterial
from .serializers import (
    SubjectSerializer, CourseSerializer, GroupSerializer, 
    EnrollmentSerializer, LearningMaterialSerializer
)
from users.permissions import IsAdminUser, IsTeacherOrAdmin
from schools.models import Branch, Classroom
from users.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from django.contrib.auth.decorators import login_required


class SubjectViewSet(viewsets.ModelViewSet):
    """ViewSet для предметов"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filterset_fields = ['school']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]

class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filterset_fields = ['subject', 'available_branches', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]

class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet для групп"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filterset_fields = ['course', 'branch', 'teacher', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Group.objects.all()
        
        # Фильтрация для преподавателей - видят только свои группы
        if self.request.user.is_teacher and not self.request.user.is_admin:
            queryset = queryset.filter(teacher=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def enroll_student(self, request, pk=None):
        """API для зачисления студента в группу"""
        group = self.get_object()
        
        if group.is_full:
            return Response(
                {"error": "Группа уже заполнена"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student_id = request.data.get('student')
        if not student_id:
            return Response(
                {"error": "ID студента не указан"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверка на уже существующее зачисление
        if Enrollment.objects.filter(student_id=student_id, group=group).exists():
            return Response(
                {"error": "Студент уже зачислен в эту группу"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment = Enrollment.objects.create(
            student_id=student_id,
            group=group,
            notes=request.data.get('notes', '')
        )
        
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet для зачислений"""
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    filterset_fields = ['student', 'group', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Enrollment.objects.all()
        
        # Студент видит только свои зачисления
        if self.request.user.is_student:
            queryset = queryset.filter(student=self.request.user)
        
        # Преподаватель видит зачисления в свои группы
        elif self.request.user.is_teacher and not self.request.user.is_admin:
            queryset = queryset.filter(group__teacher=self.request.user)
        
        return queryset

class LearningMaterialViewSet(viewsets.ModelViewSet):
    """ViewSet для учебных материалов"""
    queryset = LearningMaterial.objects.all()
    serializer_class = LearningMaterialSerializer
    filterset_fields = ['course', 'created_by']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = LearningMaterial.objects.all()
        
        # Студент видит материалы только для своих курсов
        if self.request.user.is_student:
            enrolled_courses = Course.objects.filter(
                groups__enrollments__student=self.request.user,
                groups__enrollments__is_active=True
            )
            queryset = queryset.filter(course__in=enrolled_courses)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@login_required
def add_course(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            subject_id = request.POST.get('subject')
            description = request.POST.get('description')
            price = request.POST.get('price')
            duration = request.POST.get('duration')
            duration_type = request.POST.get('duration_type')
            available_branches = request.POST.getlist('available_branches')
            is_active = request.POST.get('is_active') == 'on'

            # Create course
            course = Course.objects.create(
                name=name,
                subject_id=subject_id,
                description=description,
                price=price,
                duration=duration,
                duration_type=duration_type,
                is_active=is_active
            )

            # Add branches
            course.available_branches.set(available_branches)

            messages.success(request, 'Course added successfully!')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error adding course: {str(e)}')
            return redirect('courses:add_course')

    # GET request - show form
    context = {
        'subjects': Subject.objects.all(),
        'branches': Branch.objects.all(),
    }
    return render(request, 'courses/add_course.html', context)

@login_required
def add_group(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            course_id = request.POST.get('course')
            branch_id = request.POST.get('branch')
            teacher_id = request.POST.get('teacher')
            max_students = request.POST.get('max_students')
            is_active = request.POST.get('is_active') == 'on'

            # Create group
            group = Group.objects.create(
                name=name,
                course_id=course_id,
                branch_id=branch_id,
                teacher_id=teacher_id,
                max_students=max_students,
                is_active=is_active
            )

            messages.success(request, 'Group added successfully!')
            return redirect('scheduling:add_schedule_group', pk=group.id)
        except Exception as e:
            messages.error(request, f'Error adding group: {str(e)}')
            return redirect('courses:add_group')

    # GET request - show form
    context = {
        'courses': Course.objects.filter(is_active=True),
        'branches': Branch.objects.all(),
        'teachers': User.objects.filter(user_type='teacher'),
        'classrooms': Classroom.objects.all(),
    }
    return render(request, 'courses/add_group.html', context)

@login_required
def course_list(request):
    """
    View для отображения списка курсов
    """
    # Получаем все активные курсы
    courses = Course.objects.filter(is_active=True).select_related('subject').prefetch_related('available_branches')
    
    # Фильтрация по предмету
    subject_filter = request.GET.get('subject')
    if subject_filter:
        courses = courses.filter(subject_id=subject_filter)
    
    # Фильтрация по филиалу
    branch_filter = request.GET.get('branch')
    if branch_filter:
        courses = courses.filter(available_branches__id=branch_filter)
    
    # Поиск по названию
    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(name__icontains=search_query)
    
    # Сортировка
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price':
        courses = courses.order_by('price')
    elif sort_by == 'duration':
        courses = courses.order_by('duration')
    else:
        courses = courses.order_by('name')
    
    context = {
        'courses': courses,
        'subjects': Subject.objects.all(),
        'branches': Branch.objects.all(),
        'current_subject': subject_filter,
        'current_branch': branch_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'is_admin': request.user.is_admin or request.user.is_staff,
    }
    
    return render(request, 'courses/course_list.html', context)

@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    group.delete()
    messages.success(request, 'Группа удалена!')
    return redirect('users:groups_management')

@login_required
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.name = request.POST.get('name')
        teacher_id = request.POST.get('teacher')
        if teacher_id:
            group.teacher_id = teacher_id
        group.save()
        messages.success(request, 'Группа обновлена!')
        return redirect('users:groups_management')
    # Если GET — можно вернуть форму с текущими данными (но у нас только POST через модалку)
    return redirect('users:groups_management')

