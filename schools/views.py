# schools/views.py

from rest_framework import viewsets, permissions
from .models import School, Branch, Classroom, SchoolStaffAssignment
from .serializers import (
    SchoolSerializer, BranchSerializer, ClassroomSerializer,
    SchoolStaffAssignmentSerializer
)
from users.permissions import IsAdminUser, IsTeacherOrAdmin
from django.views.generic import TemplateView
from users.models import User
from courses.models import Course
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class SchoolViewSet(viewsets.ModelViewSet):
    """ViewSet для учебных центров"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]


class BranchViewSet(viewsets.ModelViewSet):
    """ViewSet для филиалов"""
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filterset_fields = ['school']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    


# schools/views.py (продолжение)

class ClassroomViewSet(viewsets.ModelViewSet):
    """ViewSet для аудиторий"""
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    filterset_fields = ['branch', 'is_active']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]


class SchoolStaffAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet для назначения сотрудников"""
    queryset = SchoolStaffAssignment.objects.all()
    serializer_class = SchoolStaffAssignmentSerializer
    filterset_fields = ['school', 'user', 'is_active']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = SchoolStaffAssignment.objects.all()

        # Если пользователь не админ, показываем только его назначения
        if not self.request.user.is_admin:
            queryset = queryset.filter(user=self.request.user)

        return queryset
    

class IndexView(TemplateView):
    template_name = 'school/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get teachers (users with user_type='teacher')
        context['teachers'] = User.objects.filter(user_type='teacher')[:3]
        context['courses'] = Course.objects.all()  # Get all courses
        return context


class SchoolManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'schools/management.html'

    def test_func(self):
        return self.request.user.is_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['schools'] = School.objects.prefetch_related('branches').all()
        return context

    def post(self, request, *args, **kwargs):
        print("POST DATA:", request.POST)
        # Массовое удаление филиалов
        if 'branch_ids' in request.POST:
            ids = [i for i in request.POST.get('branch_ids', '').split(',') if i.strip().isdigit()]
            print("IDS TO DELETE:", ids)
            if ids:
                # Удаляем только те филиалы, которые реально существуют
                branches_to_delete = Branch.objects.filter(id__in=ids)
                print("BRANCHES FOUND:", branches_to_delete)
                deleted_count = branches_to_delete.count()
                if deleted_count:
                    branches_to_delete.delete()
                    messages.success(request, f'Удалено филиалов: {deleted_count}')
                else:
                    messages.warning(request, 'Филиалы для удаления не найдены.')
            else:
                messages.warning(request, 'Не выбраны филиалы для удаления.')
            return redirect('school_management')
        # Добавление учебного центра
        elif 'name' in request.POST and not request.POST.get('school_id'):
            name = request.POST.get('name')
            address = request.POST.get('address', '')
            phone = request.POST.get('phone', '')
            email = request.POST.get('email', '')
            if name:
                School.objects.create(name=name, address=address, phone=phone, email=email)
                messages.success(request, f'Учебный центр "{name}" успешно добавлен.')
            else:
                messages.error(request, 'Название учебного центра обязательно.')
            return redirect('school_management')
        # Добавление филиала
        elif 'branch_name' in request.POST and request.POST.get('school_id'):
            school_id = request.POST.get('school_id')
            branch_name = request.POST.get('branch_name')
            branch_address = request.POST.get('branch_address', '')
            branch_phone = request.POST.get('branch_phone', '')
            branch_email = request.POST.get('branch_email', '')
            try:
                school = School.objects.get(id=school_id)
                if branch_name:
                    Branch.objects.create(
                        school=school,
                        name=branch_name,
                        address=branch_address,
                        phone=branch_phone,
                        email=branch_email
                    )
                    messages.success(request, f'Филиал "{branch_name}" успешно добавлен.')
                else:
                    messages.error(request, 'Название филиала обязательно.')
            except School.DoesNotExist:
                messages.error(request, 'Учебный центр не найден.')
            return redirect('school_management')
        else:
            messages.error(request, 'Некорректные данные формы.')
            return redirect('school_management')