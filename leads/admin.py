from django.contrib import admin
from .models import (
    Lead, LeadSource, LeadStatus, LeadActivity, 
    Section, ScheduleType, GroupSchedule
)

@admin.register(LeadSource)
class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    ordering = ('order',)

class LeadActivityInline(admin.TabularInline):
    model = LeadActivity
    extra = 1
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('activity_type', 'description', 'performed_by', 'created_at')
        }),
    )

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'source', 'status', 
                   'board_column', 'created_at', 'converted_to_student')
    list_filter = ('board_column', 'source', 'status', 'converted_to_student', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': (('first_name', 'last_name'), ('phone', 'email'), 'gender')
        }),
        ('Информация о лиде', {
            'fields': (('source', 'status'), 'interested_course', 'notes')
        }),
        ('Система отслеживания', {
            'fields': (('board_column', 'order_in_column'), 
                      ('converted_to_student', 'student'))
        }),
        ('Метаданные', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [LeadActivityInline]

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'column', 'order')
    list_filter = ('column',)
    search_fields = ('name',)
    ordering = ('column', 'order')

@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'activity_type', 'performed_by', 'created_at')
    list_filter = ('activity_type', 'performed_by', 'created_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'description')
    readonly_fields = ('created_at',)

@admin.register(ScheduleType)
class ScheduleTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(GroupSchedule)
class GroupScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'schedule_type', 'start_time', 'end_time')
    list_filter = ('schedule_type', 'group')
    search_fields = ('group__name', 'schedule_type__name')