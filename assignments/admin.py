from django.contrib import admin
from .models import Assignment, Submission

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'due_date', 'status', 'created_at')
    list_filter = ('status', 'group', 'created_by', 'due_date')
    search_fields = ('title', 'description', 'group__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('group', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'group')
        }),
        ('Timing', {
            'fields': ('due_date', 'status', 'max_points')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'attachment')
        }),
    )

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'points', 'graded_by', 'graded_at')
    list_filter = ('assignment__group', 'student', 'graded_by')
    search_fields = ('assignment__title', 'student__username', 'student__email', 'feedback')
    date_hierarchy = 'submitted_at'
    raw_id_fields = ('assignment', 'student', 'graded_by')
    readonly_fields = ('submitted_at', 'graded_at')
    fieldsets = (
        ('Submission Details', {
            'fields': ('assignment', 'student', 'content', 'attachment', 'submitted_at')
        }),
        ('Grading', {
            'fields': ('points', 'feedback', 'graded_by', 'graded_at')
        }),
    )
