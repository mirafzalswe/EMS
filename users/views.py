# users/views.py
from django.views.generic import TemplateView, DetailView, ListView
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model, authenticate, login, logout
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.utils import timezone
from scheduling.models import Schedule
from django.contrib import messages

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password

from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, ChangePasswordSerializer
)
from .permissions import IsAdminUser, IsOwnerOrAdmin
from scheduling.models import Lesson
from assignments.models import Assignment, AssignmentStatus, Submission
from attendance.models import Attendance
from finance.models import TeacherSalary, FuturePayment
from courses.models import Group, Course
from courses.models import Enrollment
# from grades.models import 
# from announcements.models import Announcement
from courses.models import LearningMaterial
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Course, Group, Enrollment
from scheduling.models import Lesson
from assignments.models import Assignment
from attendance.models import Attendance
from finance.models import TeacherSalary
from django.db import models
from django.db.models import Q
from courses.models import Subject, Branch
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from schools.models import Classroom

User = get_user_model()

class Home(TemplateView):
    template_name = 'base.html'


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        elif self.action == 'create':
            # Разрешаем создание учителей аутентифицированным пользователям
            return [permissions.IsAuthenticated()]
        elif self.action == 'list':
            return [permissions.IsAuthenticated()]
        elif self.action == 'view_teachers':  
            return [permissions.AllowAny()]   
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Фильтрация в зависимости от типа пользователя"""
        queryset = User.objects.all()

        # Параметры запроса
        user_type = self.request.query_params.get('user_type', None)

        # Фильтрация по типу пользователя
        if user_type is not None:
            queryset = queryset.filter(user_type=user_type)

        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получение информации о текущем пользователе"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrAdmin])
    def change_password(self, request, pk=None):
        """Изменение пароля пользователя"""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Проверка старого пароля
            if not user.check_password(serializer.data.get('old_password')):
                return Response({"old_password": ["Неверный пароль"]},
                                status=status.HTTP_400_BAD_REQUEST)

            # Установка нового пароля
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response({"status": "Пароль успешно изменен"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @action(
    detail=False,
    methods=['get'],
    url_path='teachers/list',
    renderer_classes=[TemplateHTMLRenderer, JSONRenderer]
    )
    @permission_classes([AllowAny])
    def view_teachers(self, request):
        teachers = self.get_queryset().filter(user_type='teacher')
        serializer = self.get_serializer(teachers, many=True)

        # DRF сам определит формат ответа на основе Accept-заголовка
        return Response({'teachers': serializer.data}, template_name='users/teachers.html')

    @action(
        detail=False,
        methods=['post'],
        url_path='create-teacher',
        permission_classes=[permissions.IsAuthenticated]
    )
    def create_teacher(self, request):
        """Создание нового учителя"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_type='teacher')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.shortcuts import render, redirect
from django.views import View

class LoginView(View):
    def get(self, request):
        # If user is already authenticated, redirect based on role
        if request.user.is_authenticated:
            return self._redirect_by_role(request.user)
        return render(request, 'users/login.html')
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:    
            login(request, user)
            return self._redirect_by_role(user)
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})
    
    def _redirect_by_role(self, user):
        """Redirect user based on their role"""
        if user.is_admin:
            return redirect('admin_dashboard')
        elif user.is_teacher:
            return redirect('teacher_profile')
        elif user.is_student:
            return redirect('student_dashboard')
        else:
            # For unknown roles, show error and logout
            logout(self.request)
            return render(self.request, 'users/login.html', 
                        {'error': 'Your account has an invalid role. Please contact support.'})

class BaseDashboardView(LoginRequiredMixin, TemplateView):
    """Base class for all dashboard views"""
    template_name = 'users/dashboard.html'

class AdminDashboardView(BaseDashboardView):
    """Admin dashboard view"""
    template_name = 'users/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all teachers
        teachers = User.objects.filter(user_type='teacher')
        
        # Создаем список словарей с информацией о каждом учителе и его группах
        teachers_data = []
        for teacher in teachers:
            groups = Group.objects.filter(teacher=teacher)
            teachers_data.append({
                'teacher': teacher,
                'groups': groups,
                'groups_count': groups.count()
            })
        
        context['teachers_data'] = teachers_data
        # Добавляем статистику для дашборда
        context['all_students'] = User.objects.filter(user_type='student').count()
        context['all_teachers'] = User.objects.filter(user_type='teacher').count()
        context['all_groups'] = Group.objects.count()
        context['all_courses'] = Course.objects.count()

        # --- Формируем расписание-сетку на неделю по Schedule ---
        from scheduling.models import Schedule
        schedules = Schedule.objects.select_related('group__course__subject', 'group__teacher', 'classroom')
        # Собираем все уникальные времена начала занятий
        time_set = set()
        for sched in schedules:
            time_set.add(sched.start_time)
        time_slots = sorted(list(time_set))
        time_slot_strs = [t.strftime('%H:%M:%S') for t in time_slots]
        # timetable[time][weekday] = [schedules]
        timetable = {t: {i: [] for i in range(7)} for t in time_slot_strs}
        for sched in schedules:
            time_key = sched.start_time.strftime('%H:%M:%S')
            timetable[time_key][sched.day_of_week].append(sched)
        context['time_slots'] = time_slots
        context['timetable'] = timetable
        context['weekdays'] = [
            'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba'
        ]
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        context['week_start'] = week_start
        context['week_end'] = week_end
        return context

class TeacherDashboardView(BaseDashboardView):
    """Teacher dashboard view"""
    template_name = 'users/teacher_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # # Add teacher-specific context data
        context['groups'] = self.request.user.teacher_groups.all()
        context['students'] = self.request.user.teacher_students.all()
        context['schedule'] = self.request.user.teacher_schedule.all()
        return context
    
def student_dashboard_view(request):
    context = {}
    student = request.user
    try:
        # Получаем группы студента
        student_groups = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('group', 'group__teacher')
        groups = [enrollment.group for enrollment in student_groups]
        context['student_groups'] = groups
        
        # Рассчитываем процент посещаемости
        from attendance.models import Attendance
        total_lessons = Attendance.objects.filter(student=student).count()
        present_lessons = Attendance.objects.filter(student=student, status='present').count()
        context['attendance_rate'] = (present_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        # Рассчитываем среднюю оценку
        from assignments.models import Submission
        submissions = Submission.objects.filter(student=student, points__isnull=False)
        if submissions.exists():
            total_points = sum(sub.points for sub in submissions)
            context['average_grade'] = total_points / submissions.count()
        else:
            context['average_grade'] = 0
        
        # Получаем предстоящие задания
        from assignments.models import Assignment
        group_ids = [enrollment.group.id for enrollment in student_groups]
        upcoming_assignments = Assignment.objects.filter(
            group_id__in=group_ids,
            due_date__gte=timezone.now().date()
        ).select_related('group').order_by('due_date')[:5]
        context['upcoming_assignments'] = upcoming_assignments
        
        # Получаем общее количество баллов (коины)
        context['total_points'] = submissions.aggregate(total=models.Sum('points'))['total'] or 0
        
        # Получаем последние записи посещаемости
        recent_attendance = Attendance.objects.filter(student=student).select_related(
            'lesson__schedule__group', 'lesson'
        ).order_by('-marked_at')[:5]
        context['assigments'] = recent_attendance  # Используем существующее имя переменной из шаблона
        
        # Формируем данные о платежах
        grouped_payments = []
        today = date.today()
        month_start = today.replace(day=1)
        if groups:
            for enrollment in student_groups:
                group = enrollment.group
                price = group.course.price
                payments_rows = []
                for i in range(3):
                    year = month_start.year + (month_start.month - 1 + i) // 12
                    month = (month_start.month - 1 + i) % 12 + 1
                    day = min(enrollment.enrollment_date.day, 28)
                    try:
                        pay_date = month_start.replace(year=year, month=month, day=day)
                    except ValueError:
                        pay_date = month_start.replace(year=year, month=month, day=1)
                    from finance.models import FuturePayment
                    fp = FuturePayment.objects.filter(student=student, group=group, payment_date=pay_date).first()
                    if fp:
                        payments_rows.append(fp)
                    else:
                        payments_rows.append(type('FakeFP', (), {
                            'payment_date': pay_date,
                            'amount': price,
                            'status': 'pending',
                            'id': None
                        })())
                grouped_payments.append({
                    'group': group,
                    'payments': payments_rows
                })
        context['grouped_payments'] = grouped_payments
        
    except Exception as e:
        print(f"Ошибка в student_dashboard_view: {str(e)}")
        context.update({
            'group': None,
            'schedule': [],
            'assignments': [],
            'attendance': [],
            'total_points': 0,
            'attendance_rate': 0,
            'upcoming_assignments': [],
            'recent_attendance': [],
            'grouped_payments': [],
            'assigments': [],
            'average_grade': 0
        })
    
    context['student_enrollments'] = Enrollment.objects.filter(student=student, is_active=True).select_related('group__course')
    context['student'] = student
    return render(request, 'users/student/student_dashboard.html', context)



def students_assignments(request):
    context = {}
    try:
        # First get the group IDs that the student is enrolled in
        group_ids = Enrollment.objects.filter(
            student=request.user,
            is_active=True
        ).values_list('group_id', flat=True)
        
        # Then use these group IDs to filter assignments and prefetch submissions
        assignments = Assignment.objects.filter(
            group_id__in=group_ids,
        ).select_related('group', 'created_by').prefetch_related('submissions').order_by('-due_date')
        
        # Add submission status to each assignment
        for assignment in assignments:
            try:
                submission = assignment.submissions.get(student=request.user)
                assignment.submission_status = 'completed'
                assignment.points = submission.points
                assignment.feedback = submission.feedback
                assignment.submitted_at = submission.submitted_at
            except Submission.DoesNotExist:
                assignment.submission_status = 'not_submitted'
                assignment.points = None
                assignment.feedback = None
                assignment.submitted_at = None
        context['assignments'] = assignments
    except Exception as e:
        print(f"Ошибка в students_assignments: {str(e)}")
        context.update({
            'assignments': [],
        })
    return render(request, 'users/student/students_assignments.html', context)


def student_lesson_schedule(request):
    student = request.user 
    context = {}
    
    # Get current date and calculate week start/end
    date_str = request.GET.get('date')
    if date_str:
        try:
            today = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            today = datetime.now().date()
    else:
        today = datetime.now().date()
    
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    try:
        # Get all active enrollments
        enrollments = Enrollment.objects.filter(
            student=student, 
            is_active=True
        ).select_related('group__course')
        
        weekly_schedules = []
        
        for enrollment in enrollments:
            group = enrollment.group
            # Get lessons for the current week
            lessons = Lesson.objects.filter(
                schedule__group=group,
                date__gte=week_start,
                date__lte=week_end
            ).select_related(
                'schedule__group',
                'schedule__classroom'
            ).order_by('date', 'start_time')
            
            if lessons.exists():
                weekly_schedules.append({
                    'group': group,
                    'lessons': lessons
                })
        
        context.update({
            'weekly_schedules': weekly_schedules,
            'week_start': week_start,
            'week_end': week_end,
            'today': today,
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        })
        
    except Exception as e:
        print(f"Ошибка в student_lesson_schedule: {str(e)}")
        context.update({
            'weekly_schedules': [],
            'week_start': week_start,
            'week_end': week_end,
            'today': today,
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        })
    
    return render(request, 'users/student/student_schedule.html', context)


class TeacherProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/teacher_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user
        
        # Get teaching groups
        groups = Group.objects.filter(teacher=teacher).select_related('course')
        
        # Get upcoming lessons
        upcoming_lessons = Lesson.objects.filter(
            schedule__group__teacher=teacher,
            date__gte=timezone.now().date()
        ).select_related('schedule__group', 'schedule__classroom').order_by('date', 'start_time')[:5]
        
        # Get recent assignments
        recent_assignments = Assignment.objects.filter(
            group__teacher=teacher
        ).select_related('group').order_by('-created_at')[:5]
        
        # Get recent attendance records
        recent_attendance = Attendance.objects.filter(
            lesson__schedule__group__teacher=teacher
        ).select_related('student', 'lesson__schedule__group').order_by('-marked_at')[:5]
        
        # Get latest salary information
        latest_salary = TeacherSalary.objects.filter(
            teacher=teacher
        ).order_by('-period_end').first()

        assignment_list = Assignment.objects.filter(
            group__in=groups
        )
        
        context.update({
            'teacher': teacher,
            'groups': groups,
            'upcoming_lessons': upcoming_lessons,
            'recent_assignments': recent_assignments,
            'recent_attendance': recent_attendance,
            'latest_salary': latest_salary,
        
        })
        
        return context
def assignment_list_teachers(request):
    teacher = request.user
    groups = Group.objects.filter(teacher=teacher).select_related('course')

    assignment_list = Assignment.objects.filter(
        group__in=groups
    )
    return render(request, 'users/assignment_list_teacher.html', {'assignment_list':assignment_list})
        
class CreateAssignmentView(LoginRequiredMixin, TemplateView):
    """View for creating new assignments"""
    template_name = 'users/create_assignment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(teacher=self.request.user)
        return context

class MarkAttendanceView(LoginRequiredMixin, TemplateView):
    """View for marking student attendance"""
    template_name = 'users/mark_attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = Lesson.objects.filter(
            schedule__group__teacher=self.request.user,
            date=timezone.now().date()
        )
        return context

class ScheduleClassView(LoginRequiredMixin, TemplateView):
    """View for scheduling new classes"""
    template_name = 'users/schedule_class.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(teacher=self.request.user)
        return context

class SendAnnouncementView(LoginRequiredMixin, TemplateView):
    """View for sending announcements to students"""
    template_name = 'users/send_announcement.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = Group.objects.filter(teacher=self.request.user)
        return context

class GroupDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Group
    template_name = 'users/group_detail.html'
    context_object_name = 'group'

    def test_func(self):
        group = self.get_object()
        return (self.request.user.is_teacher and group.teacher == self.request.user) or self.request.user.is_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Get upcoming lessons
        context['upcoming_lessons'] = Lesson.objects.filter(
            schedule__group=group,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]
        
        # Get recent assignments
        context['recent_assignments'] = Assignment.objects.filter(
            group=group
        ).order_by('-created_at')[:5]
        
        # Add current time for comparison
        context['now'] = timezone.now()

        # Добавить расписание группы (список Schedule)
        from scheduling.models import Schedule
        schedules = Schedule.objects.filter(group=group).order_by('day_of_week', 'start_time')
        context['group_schedules'] = schedules
        context['classrooms'] = Classroom.objects.all()
        context['days_of_week'] = [
            (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'), (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье')
        ]
        # Для формы: список словарей с данными
        context['schedules_form_data'] = [
            {
                'id': s.id,
                'day_of_week': s.day_of_week,
                'start_time': s.start_time.strftime('%H:%M'),
                'end_time': s.end_time.strftime('%H:%M'),
                'classroom_id': s.classroom.id if s.classroom else '',
                'classroom_name': s.classroom.name if s.classroom else ''
            } for s in schedules
        ]
        return context

class TeacherListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/teacher_list.html'
    context_object_name = 'teachers'

    def get_queryset(self):
        return User.objects.filter(user_type='teacher').prefetch_related(
            'teaching_groups'  # это связь из Group model
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teachers = context['teachers']
        
        # Получаем количество групп для каждого учителя
       
        teacher_groups = []
        for teacher in teachers:
            groups = Group.objects.filter(teacher=teacher)
            teacher_groups.append({
                'teacher': teacher,
                'groups_count': groups.count(),
                'groups': groups
            })
        
        context['teacher_groups'] = teacher_groups
        return context

class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'users/teacher_detail.html'
    context_object_name = 'teacher'

    def get_queryset(self):
        return User.objects.filter(user_type='teacher')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        # Получаем группы через courses.models.Group
        context['groups'] = Group.objects.filter(teacher=teacher)
        return context
    

@login_required
@user_passes_test(lambda u: u.is_admin)
def add_teacher(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validation
        if not all([username, first_name, last_name, email, phone, password, password2]):
            messages.error(request, 'All fields are required')
            return redirect('add_teacher')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('add_teacher')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('add_teacher')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('add_teacher')

        # Create teacher
        try:
            teacher = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                password=make_password(password),
                user_type='teacher',
                is_active=True
            )
            messages.success(request, f'Teacher {teacher.get_full_name()} has been added successfully')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}')
            return redirect('add_teacher')

    return render(request, 'users/add_teacher.html')


@login_required
@user_passes_test(lambda u: u.is_admin)
def add_student(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Validation
        if not all([username, first_name, last_name, email, phone, password, password2]):
            messages.error(request, 'All fields are required')
            return redirect('add_student')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('add_student')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('add_student')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('add_student')

        # Create student
        try:
            student = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                password=make_password(password),
                user_type='student',
                is_active=True
            )
            messages.success(request, f'Student {student.get_full_name()} has been added successfully')
            return redirect('students_management')
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
            return redirect('add_student')

    return render(request, 'users/add_student.html')

@login_required
def student_courses_view(request):
    """
    View для отображения курсов, групп и учителей студента
    """
    student = request.user
    
    # Получаем активные зачисления студента
    enrollments = Enrollment.objects.filter(
        student=student,
        is_active=True
    ).select_related(
        'group__course__subject',
        'group__teacher',
        'group__branch'
    ).prefetch_related('group__course__materials')
    
    # Получаем доступные курсы для записи (где есть свободные места)
    available_courses = Course.objects.filter(
        is_active=True,
        groups__is_active=True
    ).exclude(
        groups__enrollments__student=student,
        groups__enrollments__is_active=True
    ).distinct().select_related('subject').prefetch_related('available_branches')
    
    # Получаем группы с свободными местами
    available_groups = Group.objects.filter(
        course__in=available_courses,
        is_active=True
    ).select_related(
        'course__subject',
        'teacher',
        'branch'
    ).prefetch_related('enrollments')
    
    # Фильтрация доступных групп
    subject_filter = request.GET.get('subject')
    if subject_filter:
        available_groups = available_groups.filter(course__subject_id=subject_filter)
    
    branch_filter = request.GET.get('branch')
    if branch_filter:
        available_groups = available_groups.filter(branch_id=branch_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        available_groups = available_groups.filter(
            Q(course__name__icontains=search_query) |
            Q(course__subject__name__icontains=search_query) |
            Q(teacher__first_name__icontains=search_query) |
            Q(teacher__last_name__icontains=search_query)
        )
    
    # Добавляем информацию о свободных местах
    for group in available_groups:
        enrolled_count = group.enrollments.filter(is_active=True).count()
        group.available_spots = group.max_students - enrolled_count
    
    # Убираем заполненные группы
    available_groups = [group for group in available_groups if group.available_spots > 0]
    
    # Обработка записи в группу
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        if group_id:
            try:
                group = Group.objects.get(id=group_id, is_active=True)
                
                # Проверяем, не записан ли уже студент в эту группу
                if not Enrollment.objects.filter(
                    student=student,
                    group=group,
                    is_active=True
                ).exists():
                    
                    # Проверяем, есть ли свободные места
                    enrolled_count = group.enrollments.filter(is_active=True).count()
                    if enrolled_count < group.max_students:
                        
                        # Создаем зачисление
                        Enrollment.objects.create(
                            student=student,
                            group=group,
                            enrollment_date=timezone.now().date(),
                            is_active=True
                        )
                        
                        messages.success(request, f'Вы успешно записались в группу "{group.name}"!')
                        return redirect('student_courses')
                    else:
                        messages.error(request, 'К сожалению, группа уже заполнена.')
                else:
                    messages.error(request, 'Вы уже записаны в эту группу.')
                    
            except Group.DoesNotExist:
                messages.error(request, 'Группа не найдена.')
            except Exception as e:
                messages.error(request, f'Ошибка при записи в группу: {str(e)}')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'available_groups': available_groups,
        'subjects': Subject.objects.all(),
        'branches': Branch.objects.all(),
        'current_subject': subject_filter,
        'current_branch': branch_filter,
        'search_query': search_query,
    }
    
    return render(request, 'users/student/student_courses.html', context)

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_admin or getattr(user, 'is_staff', False) or user.is_superuser)

@login_required
@user_passes_test(is_admin_or_staff)
def students_management_view(request):
    """
    Представление для управления студентами
    """
    # Получаем параметры фильтрации
    search_query = request.GET.get('search', '')
    subject_filter = request.GET.get('subject', '')
    branch_filter = request.GET.get('branch', '')
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', '')
    
    # Базовый queryset студентов
    students = User.objects.filter(user_type='student')
    
    # Применяем фильтры
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    if subject_filter:
        students = students.filter(enrollments__group__course__subject_id=subject_filter).distinct()
    
    if branch_filter:
        students = students.filter(enrollments__group__branch_id=branch_filter).distinct()
    
    if group_filter:
        students = students.filter(enrollments__group_id=group_filter).distinct()
    
    if status_filter:
        if status_filter == 'active':
            students = students.filter(enrollments__is_active=True).distinct()
        elif status_filter == 'inactive':
            students = students.filter(enrollments__is_active=False).distinct()
        elif status_filter == 'no_enrollment':
            students = students.filter(enrollments__isnull=True)
    
    # Добавляем информацию о зачислениях
    for student in students:
        student.enrollments_info = student.enrollments.select_related(
            'group__course__subject', 
            'group__branch', 
            'group__teacher'
        ).filter(is_active=True)
        student.total_enrollments = student.enrollments.count()
        student.active_enrollments = student.enrollments.filter(is_active=True).count()
    
    # Пагинация
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)
    
    # Контекст для фильтров
    context = {
        'students': students_page,
        'search_query': search_query,
        'current_subject': subject_filter,
        'current_branch': branch_filter,
        'current_group': group_filter,
        'current_status': status_filter,
        'subjects': Subject.objects.all(),
        'branches': Branch.objects.all(),
        'groups': Group.objects.filter(is_active=True),
        'total_students': students.count(),
    }
    
    return render(request, 'users/students_management.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def add_student_to_group(request):
    """
    Представление для добавления студента в группу
    """
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        group_id = request.POST.get('group_id')
        
        try:
            student = User.objects.get(id=student_id, user_type='student')
            group = Group.objects.get(id=group_id, is_active=True)
            
            # Проверяем, не зачислен ли уже студент в эту группу
            if Enrollment.objects.filter(student=student, group=group).exists():
                messages.error(request, f'Студент {student.get_full_name()} уже зачислен в группу {group.name}')
            else:
                # Проверяем, есть ли свободные места
                if group.is_full:
                    messages.error(request, f'Группа {group.name} заполнена')
                else:
                    Enrollment.objects.create(student=student, group=group)
                    messages.success(request, f'Студент {student.get_full_name()} успешно зачислен в группу {group.name}')
            
        except (User.DoesNotExist, Group.DoesNotExist):
            messages.error(request, 'Студент или группа не найдены')
        
        return redirect('students_management')
    
    # GET запрос - показываем форму
    students = User.objects.filter(user_type='student').order_by('first_name', 'last_name')
    groups = Group.objects.filter(is_active=True).select_related('course', 'branch', 'teacher')
    
    # Добавляем информацию о свободных местах
    for group in groups:
        enrolled_count = group.enrollments.filter(is_active=True).count()
        group.available_spots = group.max_students - enrolled_count
    
    context = {
        'students': students,
        'groups': groups,
    }
    
    return render(request, 'users/add_student_to_group.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
@require_POST
def remove_student_from_group(request):
    """
    Представление для удаления студента из группы
    """
    enrollment_id = request.POST.get('enrollment_id')
    
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        student_name = enrollment.student.get_full_name()
        group_name = enrollment.group.name
        
        enrollment.delete()
        messages.success(request, f'Студент {student_name} удален из группы {group_name}')
        
    except Enrollment.DoesNotExist:
        messages.error(request, 'Зачисление не найдено')
    
    return redirect('students_management')

@login_required
@user_passes_test(is_admin_or_staff)
@require_POST
def delete_student(request):
    """
    Представление для удаления студента
    """
    student_id = request.POST.get('student_id')
    
    # Отладочная информация
    print(f"DEBUG: Попытка удаления студента с ID: {student_id}")
    print(f"DEBUG: Пользователь: {request.user.username}, is_admin: {request.user.is_admin}, is_staff: {getattr(request.user, 'is_staff', False)}")
    
    try:
        student = User.objects.get(id=student_id, user_type='student')
        student_name = student.get_full_name()
        
        print(f"DEBUG: Найден студент: {student_name}")
        
        # Проверяем, есть ли активные зачисления
        active_enrollments = student.enrollments.filter(is_active=True)
        if active_enrollments.exists():
            enrollment_groups = ', '.join([enrollment.group.name for enrollment in active_enrollments])
            error_msg = f'Нельзя удалить студента {student_name}. Он зачислен в группы: {enrollment_groups}. Сначала удалите его из всех групп.'
            print(f"DEBUG: {error_msg}")
            messages.error(request, error_msg)
        else:
            print(f"DEBUG: Удаляем зачисления студента")
            # Удаляем все зачисления студента
            student.enrollments.all().delete()
            print(f"DEBUG: Удаляем студента")
            # Удаляем студента
            student.delete()
            success_msg = f'Студент {student_name} успешно удален'
            print(f"DEBUG: {success_msg}")
            messages.success(request, success_msg)
        
    except User.DoesNotExist:
        error_msg = 'Студент не найден'
        print(f"DEBUG: {error_msg}")
        messages.error(request, error_msg)
    except Exception as e:
        error_msg = f'Ошибка при удалении студента: {str(e)}'
        print(f"DEBUG: {error_msg}")
        messages.error(request, error_msg)
    
    return redirect('students_management')

@login_required
@user_passes_test(is_admin_or_staff)
@require_POST
def bulk_delete_students(request):
    """
    Представление для массового удаления студентов
    """
    student_ids_str = request.POST.get('student_ids', '')
    
    print(f"DEBUG: Массовое удаление студентов. ID: {student_ids_str}")
    print(f"DEBUG: Пользователь: {request.user.username}, is_admin: {request.user.is_admin}, is_staff: {getattr(request.user, 'is_staff', False)}")
    
    if not student_ids_str:
        messages.error(request, 'Не выбраны студенты для удаления')
        return redirect('students_management')
    
    student_ids = [int(id.strip()) for id in student_ids_str.split(',') if id.strip().isdigit()]
    
    if not student_ids:
        messages.error(request, 'Некорректные ID студентов')
        return redirect('students_management')
    
    deleted_count = 0
    error_students = []
    
    for student_id in student_ids:
        try:
            student = User.objects.get(id=student_id, user_type='student')
            student_name = student.get_full_name()
            
            print(f"DEBUG: Обрабатываем студента: {student_name} (ID: {student_id})")
            
            # Проверяем, есть ли активные зачисления
            active_enrollments = student.enrollments.filter(is_active=True)
            if active_enrollments.exists():
                enrollment_groups = ', '.join([enrollment.group.name for enrollment in active_enrollments])
                error_msg = f'{student_name} (зачислен в: {enrollment_groups})'
                print(f"DEBUG: Нельзя удалить: {error_msg}")
                error_students.append(error_msg)
            else:
                print(f"DEBUG: Удаляем студента: {student_name}")
                # Удаляем все зачисления студента
                student.enrollments.all().delete()
                # Удаляем студента
                student.delete()
                deleted_count += 1
                print(f"DEBUG: Студент {student_name} успешно удален")
                
        except User.DoesNotExist:
            error_msg = f'ID: {student_id} (не найден)'
            print(f"DEBUG: {error_msg}")
            error_students.append(error_msg)
        except Exception as e:
            error_msg = f'ID: {student_id} (ошибка: {str(e)})'
            print(f"DEBUG: {error_msg}")
            error_students.append(error_msg)
    
    # Формируем сообщения
    if deleted_count > 0:
        success_msg = f'Успешно удалено {deleted_count} студента(ов)'
        print(f"DEBUG: {success_msg}")
        messages.success(request, success_msg)
    
    if error_students:
        error_message = f'Не удалось удалить следующих студентов:\n' + '\n'.join(error_students)
        print(f"DEBUG: {error_message}")
        messages.error(request, error_message)
    
    return redirect('students_management')




def groups_management(request):
    groups = Group.objects.all()
    teachers = User.objects.filter(user_type='teacher')

    return render(request, 'users/groups_management.html', {
        'groups': groups,
        'teachers': teachers

    })

