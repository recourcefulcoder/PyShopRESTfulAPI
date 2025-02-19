import datetime
from http import HTTPStatus

import api.serializers as serializers
from api.authentication import AllowOptionsOrAuthenticated
from api.models import RefreshToken
from api.utils import is_valid_uuid, user_from_refresh_token

from constance.signals import config_updated

from django.contrib.auth import authenticate, get_user_model
from django.db.models import F
from django.dispatch import receiver

from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView, Response


@receiver(config_updated)
def update_tokens(sender, key, old_value, new_value, **kwargs):
    if "refresh" in key.lower():
        RefreshToken.objects.all().update(
            expires_at=F("created_at") + datetime.timedelta(seconds=new_value)
        )


class RegisterUser(CreateAPIView):
    """
        Handling user registration

        Accepts a json-object, where two fields are required (email and password), and one is optional (username);

        However, username still has a unique constrain enabled in database, which means
        if database already contains user with empty username, providing a valid "username"
        key value on registration is required.
    """

    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserRegisterSerializer


class RetrieveUpdateUser(APIView):
    """
        Serving api/me/ endpoint simple retrieve/update view; allowed methods -
        GET and PUT. <br/> <br/>
        On both methods authentication required; authentication is JWT-based, meaning
        that for accessing an endpoint Client must send an "Authorization" http-header
        with [valid JWT access token](https://jwt.io/introduction):

        "Authorization: Bearer \<access token\>"

        on **GET** method:

        Returned value is a json-object with fields "id", "username" and
        "email"


        on **PUT** method:

        Accepts json-object with new info about user; allowed json keys (and,
        respectively, user fields allowed for updating) are:

        - username
        - email
        - password

        It is possible to pass only required for update fields; it is possible to pass
        keys different from these, yet they will be ignored.

        Returned value is a json-object with updated user information.
    """

    serializer_class = serializers.UserSerializer
    permission_classes = [AllowOptionsOrAuthenticated]

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

    def options(self, request, *args, **kwargs):
        meta = self.metadata_class()
        data = meta.determine_metadata(request, self)
        data.pop('description')
        return Response(data=data, status=HTTPStatus.OK)


@api_view(["POST"])
def login_view(request):
    """
        Endpoint handling user's login;

        Accepts a json request/ requires two fields to be included: "email" and "password"
    """
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
    """
        Returns pair of refresh token and access token;

        Accepts json-object as a request, which must have a key **_refresh\_token_**;
        if such key is not found, or it is not a valid uuid object - error is returned
    """
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
    """
        deletes user's refresh token from the system;
        accepts json-object as a request, which must contain valid uuid refresh token
        under the key of **-refresh\_token_**
    """
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
