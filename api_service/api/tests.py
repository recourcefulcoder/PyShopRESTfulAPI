import subprocess
import uuid
from http import HTTPStatus
from typing import Dict, Final

from api.models import RefreshToken
from api.views import (
    RegisterUser,
    RetrieveUpdateUser,
    login_view,
    logout_view,
    refresh_view,
)

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from parameterized import parameterized

from rest_framework.test import APIClient, APIRequestFactory, APITestCase


user_parametrization = parameterized.expand([("admin",), ("user1",)])
ADMIN_EMAIL: Final = "admin@example.com"
ADMIN_PASSWORD: Final = "admin@example.com"
ADMIN_USERNAME: Final = "admin"


class APIUnitTests(APITestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        """if user list/credentials is ever changed,
        take care of changing user_parameterization configuration!"""
        cls.redis_subprocess = subprocess.Popen(
            "redis-server --port 6379", shell=True
        )
        cls.client = APIClient()
        cls.request_factory = APIRequestFactory()

        cls.admin_pass = ADMIN_PASSWORD
        cls.admin = get_user_model().objects.create(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
        )

        cls.user1_pass = "password"
        cls.user1 = get_user_model().objects.create(
            username="user1", email="user@example.com", password=cls.user1_pass
        )

    def setUp(self) -> None:
        self.test_class = type(self)

    def get_user_tokens(self, username: str) -> Dict[str, str]:
        user = getattr(type(self), username)
        login_data = {
            "email": user.email,
            "password": getattr(type(self), f"{user.username}_pass"),
        }
        login_request = type(self).request_factory.post(
            reverse_lazy("api:login"), login_data, format="json"
        )
        login_tokens = login_view(login_request).data
        return login_tokens

    @user_parametrization
    def test_login_view_succeeds_on_valid_data(self, username):
        user = getattr(self.test_class, username)
        data = {
            "email": user.email,
            "password": getattr(self.test_class, f"{username}_pass"),
        }
        request = self.test_class.request_factory.post(
            reverse_lazy("api:login"),
            data,
            format="json",
        )
        response = login_view(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @user_parametrization
    def test_login_view_gives_tokens(self, username):
        user = getattr(self.test_class, username)
        data = {
            "email": user.email,
            "password": getattr(self.test_class, f"{username}_pass"),
        }
        request = self.test_class.request_factory.post(
            reverse_lazy("api:login"), data, format="json"
        )
        response = login_view(request)
        self.assertIn("refresh_token", response.data.keys())
        self.assertIn("access_token", response.data.keys())

    def test_login_creates_refresh_token(self):
        """Implemented for admin user only"""
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        }
        login_request = type(self).request_factory.post(
            reverse_lazy("api:login"), login_data, format="json"
        )
        login_view(login_request)
        self.assertIsNotNone(
            RefreshToken.objects.filter(user=type(self).admin).first()
        )

    @parameterized.expand(
        [
            (
                {"email": "not_an_email_even", "password": "admin"},
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {"key1": "invalid_key", "key2": "another"},
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {
                    "email": ADMIN_EMAIL,
                },
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD + "invalid_pass",
                },
                HTTPStatus.UNAUTHORIZED,
            ),
            (
                {
                    "email": "notexisting@gmail.com",
                    "password": ADMIN_PASSWORD,
                },
                HTTPStatus.UNAUTHORIZED,
            ),
        ]
    )
    def test_login_fails_on_invalid_data(self, credentials, code_expected):
        """Ran only on an admin user"""
        request = self.test_class.request_factory.post(
            reverse_lazy("api:login"), credentials, format="json"
        )
        response = login_view(request)
        self.assertEqual(response.status_code, code_expected)

    @user_parametrization
    def test_refresh_succeeds_on_valid_input(self, username):
        login_tokens = self.get_user_tokens(username)

        request = self.test_class.request_factory.post(
            reverse_lazy("api:refresh"),
            {"refresh_token": login_tokens["refresh_token"]},
            format="json",
        )
        response = refresh_view(request)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("refresh_token", response.data.keys())
        self.assertIn("access_token", response.data.keys())

    def test_refresh_fails_on_invalid_input(self):
        invalid_format_token = "invalid_format"
        invalid_token = str(uuid.uuid4())

        request_invalid_format = self.test_class.request_factory.post(
            reverse_lazy("api:refresh"),
            {"refresh_token": invalid_format_token},
            format="json",
        )
        request_invalid = self.test_class.request_factory.post(
            reverse_lazy("api:refresh"),
            {"refresh_token": invalid_token},
            format="json",
        )
        self.assertEqual(
            refresh_view(request_invalid_format).status_code,
            HTTPStatus.BAD_REQUEST,
        )
        self.assertEqual(
            refresh_view(request_invalid).status_code, HTTPStatus.UNAUTHORIZED
        )

    def test_me_endpoint_protected(self):
        request = self.test_class.request_factory.post(
            reverse_lazy("api:refresh"),
            headers={"Authorization": "Bearer invalid_access_token"},
            format="json",
        )
        self.assertEqual(
            RetrieveUpdateUser.as_view()(request).status_code,
            HTTPStatus.FORBIDDEN,
        )

    def test_me_valid_retrieve(self):
        """implemented only with admin user"""
        token = self.get_user_tokens("admin")["access_token"]
        request = self.test_class.request_factory.get(
            reverse_lazy("api:refresh"),
            headers={"Authorization": f"Bearer {token}"},
            format="json",
        )
        response_data = RetrieveUpdateUser.as_view()(request).data
        expected_data = {"id": 1, "username": "admin", "email": ADMIN_EMAIL}
        self.assertEqual(expected_data, response_data)

    def test_me_valid_update(self):
        token = self.get_user_tokens(ADMIN_USERNAME)["access_token"]

        new_username = "ADMIN2"

        request = self.test_class.request_factory.put(
            reverse_lazy("api:refresh"),
            {"username": new_username},
            headers={"Authorization": f"Bearer {token}"},
            format="json",
        )
        response = RetrieveUpdateUser.as_view()(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        admin = get_user_model().objects.filter(email=ADMIN_EMAIL).first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, new_username)

    @user_parametrization
    def test_refresh_deleted_on_logout(self, username):
        refresh_token = self.get_user_tokens(username)["refresh_token"]
        request = self.test_class.request_factory.post(
            reverse_lazy("api:logout"),
            {"refresh_token": refresh_token},
            format="json",
        )
        response = logout_view(request)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsNone(
            RefreshToken.objects.filter(token=refresh_token).first()
        )

    def test_register_on_valid_input(self):
        data = {
            "username": "naruto",
            "email": "naruto@konoha.jp",
            "password": "Dattebayo!",
        }
        request = self.test_class.request_factory.post(
            reverse_lazy("api:registration"), data, format="json"
        )
        response = RegisterUser.as_view()(request)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        naruto = get_user_model().objects.filter(username="naruto").first()
        self.assertIsNotNone(naruto)
        self.assertEqual(naruto.email, "naruto@konoha.jp")

    @parameterized.expand(
        [
            (
                {"email": "not_an_email_even", "password": "admin"},
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {"key1": "invalid_key", "key2": "another"},
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {
                    "email": ADMIN_EMAIL,
                },
                HTTPStatus.BAD_REQUEST,
            ),
            (
                {
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD,
                },
                HTTPStatus.BAD_REQUEST,
            ),
        ]
    )
    def test_register_on_invalid_data(self, data, expected_code):
        request = self.test_class.request_factory.post(
            reverse_lazy("api:registration"), data, format="json"
        )
        response = RegisterUser.as_view()(request)
        self.assertEqual(response.status_code, expected_code)
