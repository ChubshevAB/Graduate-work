from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'is_active', 'created_at', 'updated_at',
            'role_display'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_role_display(self, obj):
        if obj.is_administrator:
            return 'Администратор'
        elif obj.is_moderator:
            return 'Модератор'
        elif obj.is_regular_user:
            return 'Пользователь'
        else:
            return 'Гость'


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirmation = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'first_name', 'last_name', 'phone', 'department'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirmation']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
