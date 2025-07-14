# scheduling/serializers.py

from rest_framework import serializers
from .models import Schedule, Lesson, Event
from courses.serializers import GroupSerializer
from schools.serializers import ClassroomSerializer
from users.serializers import UserSerializer

class LessonMinimalSerializer(serializers.ModelSerializer):
    """Сериализатор для минимальной информации о занятии"""
    class Meta:
        model = Lesson
        fields = ('id', 'date', 'start_time', 'end_time', 'topic', 'is_conducted', 'canceled')
        read_only_fields = fields

class ScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания"""
    group_details = GroupSerializer(source='group', read_only=True)
    classroom_details = ClassroomSerializer(source='classroom', read_only=True)
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Schedule
        fields = ('id', 'group', 'group_details', 'classroom', 'classroom_details', 
                 'day_of_week', 'day_of_week_display', 'start_time', 'end_time', 
                 'is_active', 'created_at')
        read_only_fields = ('created_at',)

class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для занятий"""
    schedule_details = ScheduleSerializer(source='schedule', read_only=True)
    conducted_by_details = UserSerializer(source='conducted_by', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ('id', 'schedule', 'schedule_details', 'date', 'start_time', 'end_time', 
                 'topic', 'description', 'is_conducted', 'conducted_by', 
                 'conducted_by_details', 'canceled', 'cancellation_reason', 
                 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class EventSerializer(serializers.ModelSerializer):
    """Сериализатор для событий"""
    created_by_details = UserSerializer(source='created_by', read_only=True)
    participants_details = UserSerializer(source='participants', many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'start_datetime', 'end_datetime', 
                 'location', 'created_by', 'created_by_details', 'participants', 
                 'participants_details', 'is_public', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')