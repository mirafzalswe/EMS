from rest_framework import serializers
from .models import Lead, LeadSource, LeadStatus, LeadActivity, Section, ScheduleType, GroupSchedule
from courses.models import Course, Group
from users.models import User


class LeadSourceSerializer(serializers.ModelSerializer):
    """Сериализатор для источников лидов"""
    class Meta:
        model = LeadSource
        fields = ['id', 'name', 'description', 'is_active']


class LeadStatusSerializer(serializers.ModelSerializer):
    """Сериализатор для статусов лидов"""
    class Meta:
        model = LeadStatus
        fields = ['id', 'name', 'order']


class UserMinimalSerializer(serializers.ModelSerializer):
    """Минимальный сериализатор для пользователя"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'user_type']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CourseMinimalSerializer(serializers.ModelSerializer):
    """Минимальный сериализатор для курса"""
    subject_name = serializers.ReadOnlyField(source='subject.name')
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'subject_name', 'price', 'duration']


class GroupMinimalSerializer(serializers.ModelSerializer):
    """Минимальный сериализатор для группы"""
    teacher_name = serializers.ReadOnlyField(source='teacher.get_full_name')
    course_name = serializers.ReadOnlyField(source='course.name')
    branch_name = serializers.ReadOnlyField(source='branch.name')
    students_count = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    
    class Meta:
        model = Group
        fields = [
            'id', 'name', 'teacher_name', 'course_name', 
            'branch_name', 'start_date', 'end_date',
            'max_students', 'students_count', 'is_full',
            'is_active'
        ]


class LeadActivitySerializer(serializers.ModelSerializer):
    """Сериализатор для активностей лида"""
    performed_by = UserMinimalSerializer(read_only=True)
    activity_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = LeadActivity
        fields = [
            'id', 'lead', 'activity_type', 'activity_type_display',
            'description', 'performed_by', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_activity_type_display(self, obj):
        return obj.get_activity_type_display()


class LeadListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка лидов"""
    source_name = serializers.ReadOnlyField(source='source.name')
    board_column_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email',
            'source', 'source_name', 'board_column', 'board_column_display',
            'order_in_column', 'created_at', 'converted_to_student'
        ]
    
    def get_board_column_display(self, obj):
        return obj.get_board_column_display()


class LeadDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о лиде"""
    source = LeadSourceSerializer(read_only=True)
    interested_course = CourseMinimalSerializer(read_only=True)
    student = UserMinimalSerializer(read_only=True)
    activities = LeadActivitySerializer(many=True, read_only=True)
    gender_display = serializers.SerializerMethodField()
    board_column_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'phone', 'email',
            'gender', 'gender_display', 'source', 'interested_course', 
            'notes', 'board_column', 'board_column_display', 'order_in_column',
            'created_at', 'updated_at', 'converted_to_student', 'student',
            'activities'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_gender_display(self, obj):
        return dict(Lead.GENDER_CHOICES).get(obj.gender, '')
    
    def get_board_column_display(self, obj):
        return obj.get_board_column_display()


class LeadCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления лида"""
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'phone', 'email',
            'gender', 'source', 'interested_course', 'notes',
            'board_column', 'order_in_column'
        ]
    
    def create(self, validated_data):
        if 'board_column' not in validated_data:
            validated_data['board_column'] = 'new'
        
        if 'order_in_column' not in validated_data:
            # Get the max order in the column
            max_order = Lead.objects.filter(
                board_column=validated_data['board_column']
            ).aggregate(max_order=models.Max('order_in_column'))['max_order'] or 0
            validated_data['order_in_column'] = max_order + 1
        
        lead = Lead.objects.create(**validated_data)
        
        # Create activity log
        user = self.context['request'].user if 'request' in self.context else None
        if user:
            LeadActivity.objects.create(
                lead=lead,
                activity_type='status_change',
                description=f'Лид создан и добавлен в колонку "{lead.get_board_column_display()}"',
                performed_by=user
            )
        
        return lead


class SectionSerializer(serializers.ModelSerializer):
    """Сериализатор для разделов на доске"""
    column_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ['id', 'name', 'column', 'column_display', 'order', 'created_at']
        read_only_fields = ['created_at']
    
    def get_column_display(self, obj):
        return obj.get_column_display()


class ScheduleTypeSerializer(serializers.ModelSerializer):
    """Сериализатор для типов расписания"""
    class Meta:
        model = ScheduleType
        fields = ['id', 'name', 'description']


class GroupScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания групп"""
    group = GroupMinimalSerializer(read_only=True)
    schedule_type = ScheduleTypeSerializer(read_only=True)
    
    class Meta:
        model = GroupSchedule
        fields = ['id', 'group', 'schedule_type', 'start_time', 'end_time']


class LeadMoveSerializer(serializers.Serializer):
    """Сериализатор для перемещения лида между колонками"""
    lead_id = serializers.IntegerField()
    new_column = serializers.CharField()
    new_order = serializers.IntegerField()


class LeadAssignToGroupSerializer(serializers.Serializer):
    """Сериализатор для назначения лида в группу"""
    group_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)


class LeadNoteSerializer(serializers.Serializer):
    """Сериализатор для добавления заметки к лиду"""
    note = serializers.CharField()


class DashboardStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики на доске"""
    total_leads = serializers.IntegerField()
    new_count = serializers.IntegerField()
    waiting_count = serializers.IntegerField()
    trial_count = serializers.IntegerField()
    attending_count = serializers.IntegerField()
    converted_count = serializers.IntegerField()
    conversion_rate = serializers.FloatField()