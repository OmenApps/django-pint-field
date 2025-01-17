"""URLs for the laboratory app."""

from django.urls import path

import example_project.laboratory.views as views


app_name = "laboratory"


urlpatterns = [
    # Dashboard URLs
    path("", views.main_dashboard, name="dashboard"),
    path("dashboard/status/", views.system_status, name="system_status"),
    path("dashboard/stability/", views.dimensional_stability, name="dimensional_stability"),
    path("dashboard/incidents/", views.global_incident_map, name="global_incident_map"),
    # Universe URLs
    path("universes/", views.universe_list, name="universe_list"),
    path("universes/create/", views.universe_create, name="universe_create"),
    path("universes/<int:pk>/", views.universe_detail, name="universe_detail"),
    path("universes/<int:pk>/update/", views.universe_update, name="universe_update"),
    # Laboratory URLs
    path("laboratories/", views.laboratory_list, name="laboratory_list"),
    path("laboratories/create/", views.laboratory_create, name="laboratory_create"),
    path("laboratories/<int:pk>/", views.laboratory_detail, name="laboratory_detail"),
    path("laboratories/<int:pk>/update/", views.laboratory_update, name="laboratory_update"),
    # Experimental Device URLs
    path("devices/", views.device_list, name="device_list"),
    path("devices/create/", views.device_create, name="device_create"),
    path("devices/<int:pk>/", views.device_detail, name="device_detail"),
    path("devices/<int:pk>/update/", views.device_update, name="device_update"),
    # Anomalous Substance URLs
    path("substances/", views.substance_list, name="substance_list"),
    path("substances/create/", views.substance_create, name="substance_create"),
    path("substances/<int:pk>/", views.substance_detail, name="substance_detail"),
    path("substances/<int:pk>/update/", views.substance_update, name="substance_update"),
    # Test Subject URLs
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/", views.subject_detail, name="subject_detail"),
    path("subjects/<int:pk>/update/", views.subject_update, name="subject_update"),
    # Incident Report URLs
    path("incidents/", views.incident_list, name="incident_list"),
    path("incidents/create/", views.incident_create, name="incident_create"),
    path("incidents/<int:pk>/", views.incident_detail, name="incident_detail"),
    path("incidents/<int:pk>/update/", views.incident_update, name="incident_update"),
    # Dimensional Rift URLs
    path("rifts/", views.rift_list, name="rift_list"),
    path("rifts/create/", views.rift_create, name="rift_create"),
    path("rifts/<int:pk>/", views.rift_detail, name="rift_detail"),
    path("rifts/<int:pk>/update/", views.rift_update, name="rift_update"),
    # Safety Protocol URLs
    path("protocols/", views.protocol_list, name="protocol_list"),
    path("protocols/create/", views.protocol_create, name="protocol_create"),
    path("protocols/<int:pk>/", views.protocol_detail, name="protocol_detail"),
    path("protocols/<int:pk>/update/", views.protocol_update, name="protocol_update"),
    # Energy Reading URLs
    path("energy/", views.energy_list, name="energy_list"),
    path("energy/create/", views.energy_create, name="energy_create"),
    path("energy/<int:pk>/", views.energy_detail, name="energy_detail"),
    path("energy/<int:pk>/update/", views.energy_update, name="energy_update"),
    # Cheatsheet URL
    path("cheatsheet/", views.cheatsheet, name="cheatsheet"),
]
