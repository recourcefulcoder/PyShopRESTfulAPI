import api.views as views

from django.urls import path


app_name = "api"

urlpatterns = [
    path("register/", view=views.RegisterUser.as_view(), name="registration"),
    path("login/", view=views.login_view, name="login"),
    path("refresh/", view=views.refresh_token, name="refresh"),
    path("logout/", view=views.do_nothing, name="logout"),
    path(
        "me/", view=views.RetrieveUpdateUser.as_view(), name="account_options"
    ),
]
