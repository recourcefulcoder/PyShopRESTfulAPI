import datetime
from http import HTTPStatus

import api.serializers as serializers
from api.models import RefreshToken
from api.utils import user_from_refresh_token

from constance.signals import config_updated

from django.contrib.auth import authenticate, get_user_model
from django.db.models import F
from django.dispatch import receiver
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView, Response


@receiver(config_updated)
def update_tokens(sender, key, old_value, new_value, **kwargs):
    if "refresh" in key.lower():
        RefreshToken.objects.all().update(
            expires_at=F("created_at") + datetime.timedelta(seconds=new_value)
        )


def do_nothing(request):
    """default do-nothing view"""
    return HttpResponse("<h1>Snap back to reality!</h1>")


class RegisterUser(CreateAPIView):
    """Handling user registration"""

    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserRegisterSerializer


class RetrieveUpdateUser(APIView):
    """Serving api/me/ endpoint simple retrieve/update view"""

    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            data={
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            },
            status=HTTPStatus.OK,
        )

    def put(self, request):
        ser = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        if ser.is_valid():
            ser.save()
            return Response(data=ser.data, status=HTTPStatus.OK)
        return Response(ser.errors, status=HTTPStatus.BAD_REQUEST)


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        pass


@api_view(["POST"])
def login_view(request):
    data = {
        "email": request.data.get("email"),
        "password": request.data.get("password"),
    }
    credentials = serializers.LoginSerializer(data=data)
    if credentials.is_valid():
        user = authenticate(
            email=credentials.validated_data["email"],
            password=credentials.validated_data["password"],
        )
        if user:
            refresh = RefreshToken.objects.filter(user=user).first()
            if not refresh or refresh.expired():
                refresh = RefreshToken.create_refresh_token(user)
            return Response(
                data={
                    "refresh_token": refresh.token,
                    "access_token": RefreshToken.create_access_token(user),
                },
                status=HTTPStatus.OK,
            )
    return Response(
        data={"error: invalid credentials"}, status=HTTPStatus.UNAUTHORIZED
    )


@api_view(["POST"])
def refresh_token(request):
    token = RefreshToken.objects.filter(
        token=request.data.get("refresh_token")
    ).first()
    if not token:
        return Response(data={"error": "invalid refresh token"})

    if token.expired():
        token.delete()
        return Response(data={"error": "Refresh token expired"})
    user = user_from_refresh_token(token.token)
    if user is None:
        return Response(data={"error": "user doesn't exist"})
    token.delete()
    refresh = RefreshToken.create_refresh_token(user)
    return Response(
        data={
            "access_token": RefreshToken.create_access_token(user),
            "refresh_token": refresh.token,
        }
    )


@api_view(["POST"])
def logout(request):
    token_str = request.data.get("refresh_token")
    if not token_str:
        return Response(
            data={"error": "token not provided"}, status=HTTPStatus.BAD_REQUEST
        )
    token = RefreshToken.objects.filter(token=token_str).first()
    if not token:
        return Response(
            data={"error": "invalid token"}, status=HTTPStatus.UNAUTHORIZED
        )
    token.delete()
    return Response(data={"success": "user logged out"}, status=HTTPStatus.OK)
