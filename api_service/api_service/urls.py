from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", view=lambda request: redirect("api:login")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
