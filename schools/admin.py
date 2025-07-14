# schools/admin.py

from django.contrib import admin
from .models import School, Branch, Classroom, SchoolStaffAssignment

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'email', 'created_at')
    search_fields = ('name', 'address', 'email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'address', 'phone', 'email', 'manager')
    search_fields = ('name', 'address', 'email', 'school__name', 'manager__username')
    list_filter = ('school',)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'capacity', 'is_active')
    search_fields = ('name', 'branch__name')
    list_filter = ('is_active', 'branch__school')


@admin.register(SchoolStaffAssignment)
class SchoolStaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'position', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'school__name', 'position')
    list_filter = ('is_active', 'school', 'start_date', 'end_date')
