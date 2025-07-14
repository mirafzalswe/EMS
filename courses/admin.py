# courses/admin.py

from django.contrib import admin
from .models import Subject, Course, Group, Enrollment, LearningMaterial

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'created_at')
    search_fields = ('name', 'school__name')
    list_filter = ('school',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'price', 'duration', 'duration_type', 'is_active')
    search_fields = ('name', 'subject__name')
    list_filter = ('is_active', 'duration_type', 'subject__school')
    filter_horizontal = ('available_branches',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'branch', 'teacher', 'is_active', 'students_count')
    search_fields = ('name', 'course__name', 'teacher__username', 'branch__name')
    list_filter = ('is_active', 'branch__school')
    autocomplete_fields = ('teacher', 'course', 'branch')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'enrollment_date', 'is_active')
    search_fields = ('student__username', 'group__name')
    list_filter = ('is_active', 'group__course__subject__school', 'enrollment_date')
    autocomplete_fields = ('student', 'group')


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_by', 'created_at', 'updated_at')
    search_fields = ('title', 'course__name', 'created_by__username')
    list_filter = ('course__subject__school', 'created_at')
    autocomplete_fields = ('course', 'created_by')
