from http import HTTPStatus

import api.serializers as serializers
from api.models import RefreshToken
from api.utils import user_from_refresh_token

from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse

from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response


def do_nothing(request):
    """default do-nothing view"""
    return HttpResponse("<h1>Snap back to reality!</h1>")


class RegisterUser(CreateAPIView):
    """Handling user registration"""

    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserRegisterSerializer
    permission_classes = [AllowAny]


class RetrieveUpdateUser(APIView):
    """Serving api/me/ endpoint simple retrieve/update view"""

    serializer_class = serializers.UserSerializer

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


class RefreshView(APIView):
    permission_classes = [AllowAny]
    queryset = RefreshToken.objects.all()

    def post(self, request):
        print(f"started processing: {request.data.get('refresh_token')}")
        token = self.queryset.filter(
            token=request.data.get("refresh_token")
        ).first()
        print("token got")
        if not token:
            return Response(data={"error": "invalid refresh token"})

        if token.expired():
            token.delete()
            return Response(data={"error": "Refresh token expired"})
        print("extracting user")
        print(f"{token.token}, TYPE: {type(token.token)}")
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
