# attendance/admin.py

from django.contrib import admin
from .models import Attendance, AttendanceReport, AttendanceStatus

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'status', 'marked_by', 'marked_at')
    list_filter = ('status', 'lesson__schedule__group', 'lesson__date')
    search_fields = ('student__first_name', 'student__last_name', 'lesson__topic', 'comment')
    autocomplete_fields = ('student', 'lesson', 'marked_by')
    readonly_fields = ('marked_at',)
    ordering = ('-lesson__date', '-lesson__start_time')

    fieldsets = (
        (None, {
            'fields': ('student', 'lesson', 'status', 'comment')
        }),
        ('Marking Info', {
            'fields': ('marked_by', 'marked_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('group', 'start_date', 'end_date', 'created_by', 'created_at')
    search_fields = ('group__name', 'created_by__username')
    list_filter = ('group', 'created_at')
    readonly_fields = ('created_at', 'report_data')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('group', 'start_date', 'end_date')
        }),
        ('Report Metadata', {
            'fields': ('created_by', 'created_at'),
        }),
        ('Report Content', {
            'fields': ('report_data',),
            'classes': ('collapse',),
        }),
    )
