# users/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from schools.views import IndexView
from .views import (
    UserViewSet, Home, LoginView,
    AdminDashboardView, TeacherDashboardView, add_student, add_teacher, student_dashboard_view,
    TeacherProfileView, GroupDetailView, student_lesson_schedule, TeacherListView, 
    TeacherDetailView, assignment_list_teachers, student_courses_view,
    students_management_view, add_student_to_group, remove_student_from_group, delete_student,
    bulk_delete_students, students_assignments, groups_management, student_change_password,
    student_profile_edit, reveal_student_password,
)
from django.contrib.auth import views as auth_views



router = DefaultRouter()
router.register(r'', UserViewSet)
# mirafzal zor bola nega disanmi chunku u ozi ustid akop
urlpatterns = [
    path('api/', include(router.urls)), 
    path('dashboard/home', Home.as_view(), name="home"),
    path('api/teachers/list/', UserViewSet.as_view({'get': 'view_teachers'}), name='teachers-list-html'),
    path('', IndexView.as_view(), name='index'),
    
    # Authentication URLs
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    
    # Dashboard URLs
    path('admin-profile/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('teachers/', TeacherListView.as_view(), name='teacher_list'),
    path('teachers/<int:pk>/', TeacherDetailView.as_view(), name='teacher_detail'),
    path('teacher/profile/', TeacherProfileView.as_view(), name='teacher_profile'),
    path('add-teacher/', add_teacher, name='add_teacher'),
    path('add-student/', add_student, name='add_student'),
    path('group/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    path('assignment/list', assignment_list_teachers, name='assignment_list' ),
    path('groups/', groups_management, name='groups_management'),
    # students
    path('student/dashboard/', student_dashboard_view, name='student_dashboard'),
    path('student/schedule/', student_lesson_schedule, name='schedule'),
    path('student/courses/', student_courses_view, name='student_courses'),
    path('student/assignments/', students_assignments, name='students_assignments'),
    path('student/change-password/', student_change_password, name='student_change_password'),
    path('student/edit-profile/', student_profile_edit, name='student_profile_edit'),

    # Новые URL для управления студентами
    path('students/', students_management_view, name='students_management'),
    path('students/add-to-group/', add_student_to_group, name='add_student_to_group'),
    path('students/remove-from-group/', remove_student_from_group, name='remove_student_from_group'),
    path('students/delete/', delete_student, name='delete_student'),
    path('students/bulk-delete/', bulk_delete_students, name='bulk_delete_students'),
    path('reveal-student-password/', reveal_student_password, name='reveal_student_password'),
]