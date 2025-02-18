import datetime
import uuid

from constance import config

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils.timezone import now as django_now
from django.utils.translation import gettext_lazy as _

import jwt


class CustomUserManager(BaseUserManager):
    def create(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True"))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True"))

        return self.create(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


class RefreshToken(models.Model):
    user = models.OneToOneField(
        CustomUser,
        related_name="refresh_token",
        on_delete=models.CASCADE,
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    @staticmethod
    def create_access_token(user) -> str:
        exp_time = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(seconds=config.ACCESS_TOKEN_LIFETIME)
        token = jwt.encode(
            {"sub": user.email, "exp": str(int(exp_time.timestamp()))},
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        return token

    @classmethod
    def create_refresh_token(cls, user) -> "RefreshToken":
        now_time = datetime.datetime.now(tz=datetime.timezone.utc)
        refresh = cls.objects.create(
            user=user,
            created_at=now_time,
            expires_at=now_time
            + datetime.timedelta(seconds=config.REFRESH_TOKEN_LIFETIME),
        )
        return refresh

    @classmethod
    def get_token(cls, token_str: str) -> "RefreshToken":
        token = cls.objects.filter(token=uuid.UUID(token_str)).first()
        return token

    def expired(self):
        return django_now() >= self.expires_at

    def __repr__(self):
        return (
            f"User: {self.user.username}\n"
            f"Token: {self.token}\n"
            f"Created at: {self.created_at}\n"
            f"Expires at: {self.expires_at}"
        )

    def __str__(self):
        return (
            f"User: {self.user.username}\n"
            f"Token: {self.token}\n"
            f"Created at: {self.created_at}\n"
            f"Expires at: {self.expires_at}"
        )
