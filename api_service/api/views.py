import datetime
from http import HTTPStatus

from django.contrib.auth import get_user_model, authenticate
from django.http import HttpResponse

from constance import config

from rest_framework.views import APIView, Response
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    LoginSerializer,
)
from .models import RefreshToken


def do_nothing(request):
    """default do-nothing view"""
    return HttpResponse("<h1>Snap back to reality!</h1>")


class RegisterUser(CreateAPIView):
    """Handling user registration"""

    queryset = get_user_model().objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class RetrieveUpdateUser(APIView):
    """Serving api/me/ endpoint simple retrieve/update view"""

    serializer_class = UserSerializer

    def get(self, request):
        return Response(
            data={
                "id": request.user.id,
                "username": "",
                "email": request.user.email,
            },
            status=HTTPStatus.OK,
        )

    def put(self, request):
        print(request.user, request.data)
        ser = self.serializer_class(
            request.user, data=request.data, partial=True
        )
        if ser.is_valid():
            ser.save()
            return Response(data=ser.data, status=HTTPStatus.OK)
        return Response(ser.errors, status=HTTPStatus.BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credentials = LoginSerializer(data=request.data)
        if credentials.is_valid():
            user = authenticate(credentials.data)
            if user:
                now_time = datetime.datetime.now(tz=datetime.timezone.utc)
                refresh = RefreshToken.objects.create(
                    user=user,
                    created_at=now_time,
                    expires_at=now_time
                    + datetime.timedelta(
                        seconds=config.REFRESH_TOKEN_LIFETIME
                    ),
                )
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
