# courses/serializers.py

from rest_framework import serializers
from .models import Subject, Course, Group, Enrollment, LearningMaterial
from users.serializers import UserSerializer, UserMinimalSerializer


class StudentMinimalSerializer(serializers.ModelSerializer):
    """Сериализатор для минимальной информации о студенте"""
    class Meta:
        model = UserSerializer.Meta.model
        fields = ('id', 'first_name', 'last_name', 'avatar')
        read_only_fields = fields


class SubjectSerializer(serializers.ModelSerializer):
    """Сериализатор для предметов"""

    class Meta:
        model = Subject
        fields = ('id', 'name', 'description', 'school', 'created_at')
        read_only_fields = ('created_at',)


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курсов"""
    subject_details = SubjectSerializer(source='subject', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'name', 'subject', 'subject_details', 'description', 'price',
                  'duration', 'duration_type', 'available_branches', 'is_active',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class GroupSerializer(serializers.ModelSerializer):
    """Сериализатор для групп"""
    course_details = CourseSerializer(source='course', read_only=True)
    teacher_details = UserSerializer(source='teacher', read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'course', 'course_details', 'branch', 'teacher',
                  'teacher_details', 'start_date', 'end_date', 'max_students',
                  'is_active', 'created_at', 'students_count', 'is_full')
        read_only_fields = ('created_at',)


class EnrollmentSerializer(serializers.ModelSerializer):
    """Сериализатор для зачислений"""
    student_details = UserSerializer(source='student', read_only=True)
    group_details = GroupSerializer(source='group', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'student', 'student_details', 'group', 'group_details',
                  'enrollment_date', 'is_active', 'notes')
        read_only_fields = ('enrollment_date',)


class LearningMaterialSerializer(serializers.ModelSerializer):
    """Сериализатор для учебных материалов"""
    created_by_details = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = LearningMaterial
        fields = ('id', 'title', 'description', 'course', 'file', 'created_by',
                  'created_by_details', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')