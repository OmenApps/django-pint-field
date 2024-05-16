from django.conf import settings
from rest_framework import routers

from tests.demoapp.api.views import (
    BigIntegerModelViewSet,
    DecimalModelViewSet,
    IntegerModelViewSet,
)

router = routers.DefaultRouter()

router.register("integers", IntegerModelViewSet, basename="integers")
router.register("big_integers", BigIntegerModelViewSet, basename="big_integers")
router.register("decimals", DecimalModelViewSet, basename="decimals")


urlpatterns = router.urls
