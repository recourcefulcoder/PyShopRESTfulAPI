from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import RefreshToken


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
            "username",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {"write_only": True},
            "username": {"required": False},
        }


class UserSerializer(UserRegisterSerializer):
    class Meta(UserRegisterSerializer.Meta):
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {"write_only": True},
            "username": {"required": True},
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshToken
        fields = ("user", "token", "expires_at")
        extra_kwargs = {
            "user": {"read_only": True},
            "expires_at": {"read_only": True},
        }
