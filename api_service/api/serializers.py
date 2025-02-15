from django.contrib.auth import get_user_model

from rest_framework import serializers


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "password",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "password": {"write_only": True},
        }


class UserSerializer(UserRegisterSerializer):
    class Meta(UserRegisterSerializer.Meta):
        fields = (
            "id",
            "username",
            "email",
            "password",
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
