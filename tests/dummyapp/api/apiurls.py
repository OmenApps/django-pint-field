from django.conf import settings
from rest_framework import routers

from tests.dummyapp.api.views import IntegerModelViewSet, BigIntegerModelViewSet, DecimalModelViewSet

router = routers.DefaultRouter()

router.register("integers", IntegerModelViewSet, basename="integers")
router.register("big_integers", BigIntegerModelViewSet, basename="big_integers")
router.register("decimals", DecimalModelViewSet, basename="decimals")


urlpatterns = router.urls
