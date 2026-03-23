"""All views for the laboratory app."""

from example_project.laboratory.views.cheatsheet import cheatsheet
from example_project.laboratory.views.dashboard import GeoJSONEncoder
from example_project.laboratory.views.dashboard import dimensional_stability
from example_project.laboratory.views.dashboard import global_incident_map
from example_project.laboratory.views.dashboard import main_dashboard
from example_project.laboratory.views.dashboard import system_status
from example_project.laboratory.views.laboratories import laboratory_create
from example_project.laboratory.views.laboratories import laboratory_detail
from example_project.laboratory.views.laboratories import laboratory_list
from example_project.laboratory.views.laboratories import laboratory_update
from example_project.laboratory.views.other import add_laboratory_context
from example_project.laboratory.views.other import add_model_context
from example_project.laboratory.views.other import device_create
from example_project.laboratory.views.other import device_detail
from example_project.laboratory.views.other import device_list
from example_project.laboratory.views.other import device_update
from example_project.laboratory.views.other import energy_create
from example_project.laboratory.views.other import energy_detail
from example_project.laboratory.views.other import energy_list
from example_project.laboratory.views.other import energy_update
from example_project.laboratory.views.other import generic_create_view
from example_project.laboratory.views.other import generic_list_view
from example_project.laboratory.views.other import generic_update_view
from example_project.laboratory.views.other import get_laboratory_from_request
from example_project.laboratory.views.other import incident_create
from example_project.laboratory.views.other import incident_detail
from example_project.laboratory.views.other import incident_list
from example_project.laboratory.views.other import incident_update
from example_project.laboratory.views.other import protocol_create
from example_project.laboratory.views.other import protocol_detail
from example_project.laboratory.views.other import protocol_list
from example_project.laboratory.views.other import protocol_update
from example_project.laboratory.views.other import rift_create
from example_project.laboratory.views.other import rift_detail
from example_project.laboratory.views.other import rift_list
from example_project.laboratory.views.other import rift_update
from example_project.laboratory.views.other import subject_create
from example_project.laboratory.views.other import subject_detail
from example_project.laboratory.views.other import subject_list
from example_project.laboratory.views.other import subject_update
from example_project.laboratory.views.other import substance_create
from example_project.laboratory.views.other import substance_detail
from example_project.laboratory.views.other import substance_list
from example_project.laboratory.views.other import substance_update
from example_project.laboratory.views.universes import universe_create
from example_project.laboratory.views.universes import universe_detail
from example_project.laboratory.views.universes import universe_list
from example_project.laboratory.views.universes import universe_update


__all__ = [
    "GeoJSONEncoder",
    "add_laboratory_context",
    "add_model_context",
    "cheatsheet",
    "device_create",
    "device_detail",
    "device_list",
    "device_update",
    "dimensional_stability",
    "energy_create",
    "energy_detail",
    "energy_list",
    "energy_update",
    "generic_create_view",
    "generic_list_view",
    "generic_update_view",
    "get_laboratory_from_request",
    "global_incident_map",
    "incident_create",
    "incident_detail",
    "incident_list",
    "incident_update",
    "laboratory_create",
    "laboratory_detail",
    "laboratory_list",
    "laboratory_update",
    "main_dashboard",
    "protocol_create",
    "protocol_detail",
    "protocol_list",
    "protocol_update",
    "rift_create",
    "rift_detail",
    "rift_list",
    "rift_update",
    "subject_create",
    "subject_detail",
    "subject_list",
    "subject_update",
    "substance_create",
    "substance_detail",
    "substance_list",
    "substance_update",
    "system_status",
    "universe_create",
    "universe_detail",
    "universe_list",
    "universe_update",
]
