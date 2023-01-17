from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from tests.dummyapp.api.serializers import IntegerModelSerializer, BigIntegerModelSerializer, DecimalModelSerializer
from tests.dummyapp.models import IntegerPintFieldSaveModel, BigIntegerPintFieldSaveModel, DecimalPintFieldSaveModel


class IntegerModelViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = IntegerPintFieldSaveModel.objects.all()
    serializer_class = IntegerModelSerializer


class BigIntegerModelViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = BigIntegerPintFieldSaveModel.objects.all()
    serializer_class = BigIntegerModelSerializer


class DecimalModelViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "id"
    pagination_class = PageNumberPagination

    queryset = DecimalPintFieldSaveModel.objects.all()
    serializer_class = DecimalModelSerializer
