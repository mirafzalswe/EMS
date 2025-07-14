# users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    """Сериализатор для минимальной информации о пользователе"""
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'user_type', 'avatar')
        read_only_fields = fields

class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с базовой информацией"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type',
                 'phone', 'avatar', 'date_joined')
        read_only_fields = ('date_joined',)

class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о пользователе"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'user_type',
                 'phone', 'birthday', 'avatar', 'bio', 'specialization', 'experience',
                 'email_notifications', 'sms_notifications', 'date_joined')
        read_only_fields = ('date_joined',)

class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password',
                 'first_name', 'last_name', 'user_type', 'phone')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            user_type=validated_data['user_type'],
            phone=validated_data.get('phone', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления данных пользователя"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'birthday', 'avatar',
                 'bio', 'specialization', 'experience', 'email_notifications',
                 'sms_notifications')

class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "Пароли не совпадают"})
        return attrs

class UserLightSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for basic user information.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'user_type', 'avatar', 'phone'
        ]
        read_only_fields = ['id', 'username', 'user_type']