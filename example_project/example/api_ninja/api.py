"""API endpoints using django-ninja."""

from typing import List

from django.shortcuts import get_object_or_404
from ninja import NinjaAPI
from ninja.pagination import PageNumberPagination

from example_project.example.models import BigIntegerPintFieldSaveModel
from example_project.example.models import DecimalPintFieldSaveModel
from example_project.example.models import IntegerPintFieldSaveModel

from .schemas import BigIntegerWeight
from .schemas import DecimalWeight
from .schemas import IntegerWeight


api = NinjaAPI(urls_namespace="api_ninja")


# Custom paginator to match DRF's behavior
class CustomPagination(PageNumberPagination):
    """Paginator matching DRF's default pagination."""

    page_size = 100  # Adjust this to match your DRF settings


@api.get("/integers", response=List[IntegerWeight])
def list_integers(request, **kwargs):
    """List all integer weight models."""
    return IntegerPintFieldSaveModel.objects.all()


@api.get("/integers/{id}", response=IntegerWeight)
def get_integer(request, id: int):
    """Get a specific integer weight model."""
    return get_object_or_404(IntegerPintFieldSaveModel, id=id)


@api.get("/big_integers", response=List[BigIntegerWeight])
def list_big_integers(request, **kwargs):
    """List all big integer weight models."""
    return BigIntegerPintFieldSaveModel.objects.all()


@api.get("/big_integers/{id}", response=BigIntegerWeight)
def get_big_integer(request, id: int):
    """Get a specific big integer weight model."""
    return get_object_or_404(BigIntegerPintFieldSaveModel, id=id)


@api.get("/decimals", response=List[DecimalWeight])
def list_decimals(request, **kwargs):
    """List all decimal weight models."""
    return DecimalPintFieldSaveModel.objects.all()


@api.get("/decimals/{id}", response=DecimalWeight)
def get_decimal(request, id: int):
    """Get a specific decimal weight model."""
    return get_object_or_404(DecimalPintFieldSaveModel, id=id)
