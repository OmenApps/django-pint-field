"""URLs for the example app's API."""

from rest_framework import routers

from example_project.example.api.views import BigIntegerModelViewSet
from example_project.example.api.views import DecimalModelViewSet
from example_project.example.api.views import GeneralIntegerModelViewSet
from example_project.example.api.views import IntegerModelViewSet


router = routers.DefaultRouter()

router.register("api/general_integers", GeneralIntegerModelViewSet, basename="general_integers")
router.register("api/integers", IntegerModelViewSet, basename="integers")
router.register("api/big_integers", BigIntegerModelViewSet, basename="big_integers")
router.register("api/decimals", DecimalModelViewSet, basename="decimals")


urlpatterns = router.urls
