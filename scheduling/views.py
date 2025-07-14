# scheduling/views.py

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime
from .models import Schedule, Lesson, Event
from .serializers import ScheduleSerializer, LessonSerializer, EventSerializer
from users.permissions import IsTeacherOrAdmin
from django_filters.rest_framework import DjangoFilterBackend

class ScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet для расписания"""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'classroom', 'day_of_week', 'is_active']
    ordering_fields = ['day_of_week', 'start_time']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Schedule.objects.all()
        
        # Студент видит расписание только своих групп
        if self.request.user.is_student:
            queryset = queryset.filter(group__enrollments__student=self.request.user,
                                     group__enrollments__is_active=True)
        
        # Преподаватель видит расписание своих групп
        elif self.request.user.is_teacher and not self.request.user.is_admin:
            queryset = queryset.filter(group__teacher=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def generate_lessons(self, request, pk=None):
        """Генерация занятий на основе расписания"""
        schedule = self.get_object()
        
        # Получаем параметры из запроса
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Необходимо указать начальную и конечную даты"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Неверный формат даты. Используйте YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Генерируем занятия
        current_date = start_date
        created_lessons = []
        
        while current_date <= end_date:
            # Проверяем, совпадает ли день недели
            if current_date.weekday() == schedule.day_of_week:
                # Проверяем, не существует ли уже занятие в этот день
                if not Lesson.objects.filter(schedule=schedule, date=current_date).exists():
                    lesson = Lesson.objects.create(
                        schedule=schedule,
                        date=current_date,
                        start_time=schedule.start_time,
                        end_time=schedule.end_time
                    )
                    created_lessons.append(lesson)
            
            current_date += timedelta(days=1)
        
        serializer = LessonSerializer(created_lessons, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet для занятий"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['schedule', 'schedule__group', 'date', 'is_conducted', 'canceled']
# scheduling/views.py (continuing from line 93)
    ordering_fields = ['date', 'start_time', 'created_at']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Lesson.objects.all()
        
        # Фильтрация по датам
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Студент видит занятия только своих групп
        if self.request.user.is_student:
            queryset = queryset.filter(
                schedule__group__enrollments__student=self.request.user,
                schedule__group__enrollments__is_active=True
            )
        
        # Преподаватель видит занятия своих групп
        elif self.request.user.is_teacher and not self.request.user.is_admin:
            queryset = queryset.filter(schedule__group__teacher=self.request.user)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_conducted(self, request, pk=None):
        """Отметить занятие как проведенное"""
        lesson = self.get_object()
        
        if not (request.user.is_admin or request.user == lesson.schedule.group.teacher):
            return Response(
                {"error": "У вас нет прав для выполнения этого действия"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        lesson.is_conducted = True
        lesson.conducted_by = request.user
        lesson.save()
        
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel_lesson(self, request, pk=None):
        """Отменить занятие"""
        lesson = self.get_object()
        
        if not (request.user.is_admin or request.user == lesson.schedule.group.teacher):
            return Response(
                {"error": "У вас нет прав для выполнения этого действия"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason')
        if not reason:
            return Response(
                {"error": "Необходимо указать причину отмены"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lesson.canceled = True
        lesson.cancellation_reason = reason
        lesson.save()
        
        serializer = self.get_serializer(lesson)
        return Response(serializer.data)

class EventViewSet(viewsets.ModelViewSet):
    """ViewSet для событий"""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'created_by']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_datetime', 'created_at']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = Event.objects.all()
        
        # Фильтрация по датам
        start_date = self.request.query_params.get('start_datetime')
        end_date = self.request.query_params.get('end_datetime')
        
        if start_date:
            queryset = queryset.filter(start_datetime__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_datetime__lte=end_date)
        
        # Пользователь видит:
        # 1. Публичные события
        # 2. События, где он участник
        # 3. События, которые он создал
        if not self.request.user.is_admin:
            queryset = queryset.filter(
                Q(is_public=True) |
                Q(participants=self.request.user) |
                Q(created_by=self.request.user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join_event(self, request, pk=None):
        """Присоединиться к событию"""
        event = self.get_object()
        
        if request.user in event.participants.all():
            return Response(
                {"error": "Вы уже участвуете в этом событии"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.participants.add(request.user)
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def leave_event(self, request, pk=None):
        """Покинуть событие"""
        event = self.get_object()
        
        if request.user not in event.participants.all():
            return Response(
                {"error": "Вы не являетесь участником этого события"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.participants.remove(request.user)
        serializer = self.get_serializer(event)
        return Response(serializer.data)


from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Schedule
from .forms import ScheduleForm
from courses.models import Group

@login_required
def add_schedule_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if not request.user.is_admin and not request.user.is_teacher:
        messages.error(request, _('У вас нет прав для добавления расписания'))
        return redirect('group_detail', pk=pk)
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, group=group)
        if form.is_valid():
            try:
                schedules = form.save(commit=True)
                if schedules:
                    messages.success(request, _('{count} расписаний успешно добавлены').format(count=len(schedules)))
                    return redirect('group_detail', pk=pk)
                else:
                    messages.error(request, _('Не удалось добавить расписание'))
            except Exception as e:
                messages.error(request, f'Ошибка при создании расписания: {str(e)}')
    else:
        form = ScheduleForm(group=group)
    
    return render(request, 'scheduling/add_schedule_group.html', {
        'form': form,
        'group': group,
        'pk': pk
    })