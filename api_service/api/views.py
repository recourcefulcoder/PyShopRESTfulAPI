import datetime
from http import HTTPStatus

import api.serializers as serializers
from api.models import RefreshToken
from api.utils import is_valid_uuid, user_from_refresh_token

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
                    "refresh_token": str(refresh.token),
                    "access_token": RefreshToken.create_access_token(user),
                },
                status=HTTPStatus.OK,
            )

        return Response(
            data={"error": "invalid credentials: user not found"},
            status=HTTPStatus.UNAUTHORIZED,
        )
    return Response(
        data={
            "error": "invalid credentials: "
                     "email omitted or invalid/password omitted"
        },
        status=HTTPStatus.BAD_REQUEST,
    )


@api_view(["POST"])
def refresh_view(request):

    if request.data.get("refresh_token") is None or not is_valid_uuid(
        request.data.get("refresh_token")
    ):
        return Response(
            data={
                "error": "invalid 'refresh_token' value "
                         "- valid uuid must be provided"
            },
            status=HTTPStatus.BAD_REQUEST,
        )
    token = RefreshToken.objects.filter(
        token=request.data.get("refresh_token")
    ).first()
    if not token:
        return Response(
            data={"error": "refresh token doesn't exist"},
            status=HTTPStatus.UNAUTHORIZED,
        )

    if token.expired():
        token.delete()
        return Response(
            data={"error": "Refresh token expired"},
            status=HTTPStatus.UNAUTHORIZED,
        )
    user = user_from_refresh_token(token.token)
    if user is None:
        return Response(
            data={"error": "user doesn't exist"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    token.delete()
    refresh = RefreshToken.create_refresh_token(user)
    return Response(
        data={
            "access_token": RefreshToken.create_access_token(user),
            "refresh_token": refresh.token,
        },
        status=HTTPStatus.OK,
    )


@api_view(["POST"])
def logout_view(request):
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
