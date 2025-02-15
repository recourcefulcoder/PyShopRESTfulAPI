from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

import api.views as views

app_name = "api"

urlpatterns = [
    path("register/", view=views.RegisterUser.as_view(), name="registration"),
    path("login/", view=TokenObtainPairView.as_view(), name="login"),
    path("refresh/", view=TokenRefreshView.as_view(), name="refresh"),
    path("logout/", view=views.do_nothing, name="logout"),
    path(
        "me/", view=views.RetrieveUpdateUser.as_view(), name="account_options"
    ),
]
