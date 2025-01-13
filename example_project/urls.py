"""URL configuration for core project."""

from django.contrib import admin
from django.urls import include
from django.urls import path

from example_project.example.api.apiurls import urlpatterns as api_urls
from example_project.example.api_ninja.api import api


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("example_project.laboratory.urls", namespace="laboratory")),
    path("example/", include("example_project.example.urls", namespace="example")),
    path("api_ninja/", api.urls),
] + api_urls
