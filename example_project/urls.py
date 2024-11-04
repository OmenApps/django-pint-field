"""URL configuration for core project."""

from django.contrib import admin
from django.urls import include
from django.urls import path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("example_project.example.urls", namespace="example")),
]
