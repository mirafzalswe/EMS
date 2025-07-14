# schools/serializers.py

from rest_framework import serializers
from .models import School, Branch, Classroom, SchoolStaffAssignment
from users.serializers import UserSerializer


class ClassroomSerializer(serializers.ModelSerializer):
    """Сериализатор для учебных аудиторий"""

    class Meta:
        model = Classroom
        fields = ('id', 'name', 'branch', 'capacity', 'description', 'is_active')


class BranchSerializer(serializers.ModelSerializer):
    """Сериализатор для филиалов учебных центров"""
    classrooms = ClassroomSerializer(many=True, read_only=True)
    manager_details = UserSerializer(source='manager', read_only=True)

    class Meta:
        model = Branch
        fields = ('id', 'name', 'school', 'address', 'phone', 'email',
                  'manager', 'manager_details', 'classrooms')


class SchoolSerializer(serializers.ModelSerializer):
    """Сериализатор для учебных центров"""
    branches = BranchSerializer(many=True, read_only=True)

    class Meta:
        model = School
        fields = ('id', 'name', 'description', 'address', 'phone', 'email',
                  'website', 'logo', 'created_at', 'updated_at', 'branches')
        read_only_fields = ('created_at', 'updated_at')


class SchoolStaffAssignmentSerializer(serializers.ModelSerializer):
    """Сериализатор для назначения сотрудников"""
    user_details = UserSerializer(source='user', read_only=True)
    school_details = serializers.StringRelatedField(source='school', read_only=True)

    class Meta:
        model = SchoolStaffAssignment
        fields = ('id', 'school', 'school_details', 'user', 'user_details',
                  'position', 'start_date', 'end_date', 'is_active')