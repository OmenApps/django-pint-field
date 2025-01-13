"""URLs for the laboratory app."""

from django.urls import path

from .views import device_create
from .views import device_detail
from .views import device_list
from .views import device_update
from .views import dimensional_stability
from .views import energy_create
from .views import energy_detail
from .views import energy_list
from .views import energy_update
from .views import global_incident_map
from .views import incident_create
from .views import incident_detail
from .views import incident_list
from .views import incident_update
from .views import laboratory_create
from .views import laboratory_detail
from .views import laboratory_list
from .views import laboratory_update
from .views import main_dashboard
from .views import protocol_create
from .views import protocol_detail
from .views import protocol_list
from .views import protocol_update
from .views import rift_create
from .views import rift_detail
from .views import rift_list
from .views import rift_update
from .views import subject_create
from .views import subject_detail
from .views import subject_list
from .views import subject_update
from .views import substance_create
from .views import substance_detail
from .views import substance_list
from .views import substance_update
from .views import system_status
from .views import universe_create
from .views import universe_detail
from .views import universe_list
from .views import universe_update


app_name = "laboratory"


urlpatterns = [
    # Universe URLs
    path("universes/", universe_list, name="universe_list"),
    path("universes/create/", universe_create, name="universe_create"),
    path("universes/<int:pk>/", universe_detail, name="universe_detail"),
    path("universes/<int:pk>/update/", universe_update, name="universe_update"),
    # Laboratory URLs
    path("laboratories/", laboratory_list, name="laboratory_list"),
    path("laboratories/create/", laboratory_create, name="laboratory_create"),
    path("laboratories/<int:pk>/", laboratory_detail, name="laboratory_detail"),
    path("laboratories/<int:pk>/update/", laboratory_update, name="laboratory_update"),
    # Dashboard URLs
    path("dashboard/", main_dashboard, name="dashboard"),
    path("dashboard/status/", system_status, name="system_status"),
    path("dashboard/stability/", dimensional_stability, name="dimensional_stability"),
    path("dashboard/incidents/", global_incident_map, name="global_incident_map"),
    # Experimental Device URLs
    path("devices/", device_list, name="device_list"),
    path("devices/create/", device_create, name="device_create"),
    path("devices/<int:pk>/", device_detail, name="device_detail"),
    path("devices/<int:pk>/update/", device_update, name="device_update"),
    # Anomalous Substance URLs
    path("substances/", substance_list, name="substance_list"),
    path("substances/create/", substance_create, name="substance_create"),
    path("substances/<int:pk>/", substance_detail, name="substance_detail"),
    path("substances/<int:pk>/update/", substance_update, name="substance_update"),
    # Test Subject URLs
    path("subjects/", subject_list, name="subject_list"),
    path("subjects/create/", subject_create, name="subject_create"),
    path("subjects/<int:pk>/", subject_detail, name="subject_detail"),
    path("subjects/<int:pk>/update/", subject_update, name="subject_update"),
    # Incident Report URLs
    path("incidents/", incident_list, name="incident_list"),
    path("incidents/create/", incident_create, name="incident_create"),
    path("incidents/<int:pk>/", incident_detail, name="incident_detail"),
    path("incidents/<int:pk>/update/", incident_update, name="incident_update"),
    # Dimensional Rift URLs
    path("rifts/", rift_list, name="rift_list"),
    path("rifts/create/", rift_create, name="rift_create"),
    path("rifts/<int:pk>/", rift_detail, name="rift_detail"),
    path("rifts/<int:pk>/update/", rift_update, name="rift_update"),
    # Safety Protocol URLs
    path("protocols/", protocol_list, name="protocol_list"),
    path("protocols/create/", protocol_create, name="protocol_create"),
    path("protocols/<int:pk>/", protocol_detail, name="protocol_detail"),
    path("protocols/<int:pk>/update/", protocol_update, name="protocol_update"),
    # Energy Reading URLs
    path("energy/", energy_list, name="energy_list"),
    path("energy/create/", energy_create, name="energy_create"),
    path("energy/<int:pk>/", energy_detail, name="energy_detail"),
    path("energy/<int:pk>/update/", energy_update, name="energy_update"),
]
