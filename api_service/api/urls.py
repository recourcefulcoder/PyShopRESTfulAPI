from django.urls import path

import api.views as views

app_name = "api"

urlpatterns = [
    path("register/", view=views.do_nothing, name="registration"),
    path("login/", view=views.do_nothing, name="login"),
    path("refresh/", view=views.do_nothing, name="refresh"),
    path("logout/", view=views.do_nothing, name="logout"),
    path("me/", view=views.UserRetrieveUpdateView.as_view(), name="get-info"),
]
