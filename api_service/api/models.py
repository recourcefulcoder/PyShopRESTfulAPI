import uuid
import datetime

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now as django_now
from django.db import models
from django.conf import settings

from constance import config

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
        token = jwt.encode(
            {
                "user_email": user.email,
                "exp": datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(seconds=config.ACCESS_TOKEN_LIFETIME),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        return token

    def is_valid(self):
        return django_now() < self.expires_at
