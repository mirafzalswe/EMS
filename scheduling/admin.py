# scheduling/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Schedule, Lesson, Event

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'get_day_display', 'start_time', 'end_time', 
                   'classroom', 'is_active')
    list_filter = ('is_active', 'day_of_week', 'group__course', 'classroom')
    search_fields = ('group__name', 'classroom__name')
    raw_id_fields = ('group', 'classroom')
    ordering = ('day_of_week', 'start_time')
    
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_display.short_description = _('День недели')
    
    fieldsets = (
        (None, {
            'fields': ('group', 'classroom')
        }),
        (_('Расписание'), {
            'fields': ('day_of_week', 'start_time', 'end_time')
        }),
        (_('Статус'), {
            'fields': ('is_active',)
        })
    )

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('get_group', 'date', 'start_time', 'end_time', 
                   'topic', 'is_conducted', 'is_canceled')
    list_filter = ('is_conducted', 'is_canceled', 'date', 
                  'schedule__group__course')
    search_fields = ('topic', 'description', 'schedule__group__name')
    raw_id_fields = ('schedule', 'conducted_by')
    date_hierarchy = 'date'
    
    def get_group(self, obj):
        return obj.schedule.group.name
    get_group.short_description = _('Группа')
    
    fieldsets = (
        (None, {
            'fields': ('schedule', 'date')
        }),
        (_('Время'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Содержание'), {
            'fields': ('topic', 'description', 'homework')
        }),
        (_('Статус'), {
            'fields': ('is_conducted', 'conducted_by', 'is_canceled', 'cancel_reason')
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_conducted:  # Если занятие уже проведено
            return ('schedule', 'date', 'start_time', 'end_time')
        return super().get_readonly_fields(request, obj)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 
                   'location', 'created_by', 'is_public')
    list_filter = ('is_public', 'created_at', 'start_datetime')
    search_fields = ('title', 'description', 'location')
    raw_id_fields = ('created_by',)
    filter_horizontal = ('participants',)
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        (_('Время и место'), {
            'fields': ('start_datetime', 'end_datetime', 'location')
        }),
        (_('Участники'), {
            'fields': ('created_by', 'participants')
        }),
        (_('Настройки'), {
            'fields': ('is_public',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый объект
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(created_by=request.user)
        return qs

# Дополнительные действия для админки
@admin.action(description=_('Отметить выбранные занятия как проведенные'))
def mark_as_conducted(modeladmin, request, queryset):
    queryset.update(is_conducted=True, conducted_by=request.user)

@admin.action(description=_('Отметить выбранные занятия как не проведенные'))
def mark_as_not_conducted(modeladmin, request, queryset):
    queryset.update(is_conducted=False, conducted_by=None)

# Добавляем действия в LessonAdmin
LessonAdmin.actions = [mark_as_conducted, mark_as_not_conducted]