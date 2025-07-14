from rest_framework import serializers
from .models import Assignment, Submission, AssignmentStatus
from courses.serializers import GroupSerializer
from scheduling.serializers import LessonMinimalSerializer
from users.serializers import UserMinimalSerializer

class AssignmentSerializer(serializers.ModelSerializer):
    """Сериализатор для заданий"""
    group_details = GroupSerializer(source='group', read_only=True)
    lesson_details = LessonMinimalSerializer(source='lesson', read_only=True)
    created_by_details = UserMinimalSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    submissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'group', 'group_details', 'lesson', 
            'lesson_details', 'due_date', 'max_points', 'status', 'status_display',
            'created_by', 'created_by_details', 'created_at', 'updated_at',
            'attachment', 'submissions_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'submissions_count']

    def get_submissions_count(self, obj):
        return obj.submissions.count()

class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заданий"""
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'group', 'lesson', 'due_date', 
            'max_points', 'status', 'attachment'
        ]

class SubmissionSerializer(serializers.ModelSerializer):
    """Сериализатор для отправленных работ"""
    assignment_details = AssignmentSerializer(source='assignment', read_only=True)
    student_details = UserMinimalSerializer(source='student', read_only=True)
    graded_by_details = UserMinimalSerializer(source='graded_by', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'assignment_details', 'student', 'student_details',
            'content', 'attachment', 'points', 'feedback', 'submitted_at',
            'graded_at', 'graded_by', 'graded_by_details'
        ]
        read_only_fields = ['submitted_at', 'graded_at']

class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания отправки работы"""
    class Meta:
        model = Submission
        fields = ['assignment', 'content', 'attachment']

class SubmissionGradeSerializer(serializers.ModelSerializer):
    """Сериализатор для оценки работы"""
    class Meta:
        model = Submission
        fields = ['points', 'feedback']
        read_only_fields = ['assignment', 'student', 'content', 'attachment', 'submitted_at']

class AssignmentStatusSerializer(serializers.Serializer):
    """Сериализатор для получения списка статусов заданий"""
    value = serializers.CharField()
    display_name = serializers.CharField()

    @classmethod
    def get_statuses(cls):
        return [
            {'value': status.value, 'display_name': status.label}
            for status in AssignmentStatus
        ] 