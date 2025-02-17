import api.views as views

from django.urls import path


app_name = "api"

urlpatterns = [
    path("register/", view=views.RegisterUser.as_view(), name="registration"),
    path("login/", view=views.LoginView.as_view(), name="login"),
    path("refresh/", view=views.RefreshView.as_view(), name="refresh"),
    path("logout/", view=views.do_nothing, name="logout"),
    path(
        "me/", view=views.RetrieveUpdateUser.as_view(), name="account_options"
    ),
]
