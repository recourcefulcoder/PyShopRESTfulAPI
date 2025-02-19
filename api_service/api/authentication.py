from api.models import CustomUser

from django.conf import settings

import jwt

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()

            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            user = CustomUser.objects.get(email=payload["sub"])
            return user, None
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.DecodeError:
            raise AuthenticationFailed("Invalid token")
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed("Invalid credentials")


class AllowOptionsOrAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if request.method == "OPTIONS":
            return True
        return request.user and request.user.is_authenticated
