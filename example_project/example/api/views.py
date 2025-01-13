"""API Views for the example app."""

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from example_project.example.api.serializers import BigIntegerModelSerializer
from example_project.example.api.serializers import DecimalModelSerializer
from example_project.example.api.serializers import GeneralIntegerModelSerializer
from example_project.example.api.serializers import IntegerModelSerializer
from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel


class GeneralIntegerModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for IntegerPintFieldSaveModel."""

    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = IntegerPintFieldSaveModel.objects.all()
    serializer_class = GeneralIntegerModelSerializer


class IntegerModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for IntegerPintFieldSaveModel."""

    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = IntegerPintFieldSaveModel.objects.all()
    serializer_class = IntegerModelSerializer


class BigIntegerModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for BigIntegerPintFieldSaveModel."""

    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = BigIntegerPintFieldSaveModel.objects.all()
    serializer_class = BigIntegerModelSerializer


class DecimalModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for DecimalPintFieldSaveModel."""

    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = DecimalPintFieldSaveModel.objects.all()
    serializer_class = DecimalModelSerializer
