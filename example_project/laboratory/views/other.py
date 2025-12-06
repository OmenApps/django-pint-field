"""Utility functions for laboratory management views."""

import logging
from decimal import Decimal
from typing import Any
from typing import Dict
from typing import Optional

from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Model
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from example_project.laboratory.forms import AnomalousSubstanceForm
from example_project.laboratory.forms import DimensionalRiftForm
from example_project.laboratory.forms import EnergyReadingForm
from example_project.laboratory.forms import ExperimentalDeviceForm
from example_project.laboratory.forms import IncidentReportForm
from example_project.laboratory.forms import SafetyProtocolForm
from example_project.laboratory.forms import ExperimentSubjectForm
from example_project.laboratory.models import AnomalousSubstance
from example_project.laboratory.models import DimensionalRift
from example_project.laboratory.models import EnergyReading
from example_project.laboratory.models import ExperimentalDevice
from example_project.laboratory.models import IncidentReport
from example_project.laboratory.models import Laboratory
from example_project.laboratory.models import SafetyProtocol
from example_project.laboratory.models import ExperimentSubject


logger = logging.getLogger(__name__)


def get_laboratory_from_request(request: WSGIRequest) -> Optional[Laboratory]:
    """Get laboratory from request query parameters."""
    laboratory_id = request.GET.get("laboratory")
    if laboratory_id:
        return get_object_or_404(Laboratory, pk=laboratory_id)
    return None


def add_laboratory_context(context: Dict[str, Any], laboratory: Optional[Laboratory]) -> Dict[str, Any]:
    """Add laboratory to context if available."""
    if laboratory:
        context["laboratory"] = laboratory
    return context


def add_model_context(context: Dict[str, Any], model: Model) -> Dict[str, Any]:
    """Add model information to context."""
    context["model_name"] = model._meta.verbose_name
    context["model_name_plural"] = model._meta.verbose_name_plural
    return context


def generic_list_view(
    request: WSGIRequest,
    model: Model,
    template_name: str = "laboratory/other/list.html",
    queryset: Optional[QuerySet] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    create_url_name: Optional[str] = None,
    update_url_name: Optional[str] = None,
    display_field: Optional[str] = None,
    display_field_name: Optional[str] = None,
) -> HttpResponse:
    """Generic list view for laboratory items."""
    # Get base queryset
    if queryset is None:
        queryset = model.objects.all()

    # Get laboratory if specified
    laboratory = get_laboratory_from_request(request)
    if laboratory:
        queryset = queryset.filter(laboratory=laboratory)

    # Prepare context
    context = extra_context or {}
    context = add_laboratory_context(context, laboratory)
    context = add_model_context(context, model)

    # Add URL names
    if create_url_name:
        context["create_url"] = create_url_name
    if update_url_name:
        context["update_url"] = update_url_name

    # Add display field info
    context["display_field"] = display_field or "name"
    context["display_field_name"] = display_field_name or "Name"

    # Add list of timestamp fields for proper formatting
    context["timestamp_fields"] = ["timestamp", "detected_at", "creation_date"]

    context["items"] = queryset

    return TemplateResponse(request, template_name, context)


def generic_create_view(
    request: WSGIRequest,
    model: Model,
    form_class: Any,
    template_name: str = "laboratory/other/form.html",
    extra_context: Optional[Dict[str, Any]] = None,
    success_url: Optional[str] = None,
) -> HttpResponse:
    """Generic create view for laboratory items."""
    # Handle form
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"{model._meta.verbose_name.title()} created successfully!")
            return redirect(success_url or item.get_absolute_url())
        else:
            logger.error("Error creating %s: %s", model._meta.verbose_name, form.errors)
            messages.error(request, f"Please correct the errors: {form.errors}")
    else:
        # Pre-set laboratory if specified
        initial = {}
        laboratory = get_laboratory_from_request(request)
        if laboratory:
            initial["laboratory"] = laboratory.pk
        form = form_class(initial=initial)

    # Prepare context
    context = extra_context or {}
    context = add_laboratory_context(context, get_laboratory_from_request(request))
    context = add_model_context(context, model)
    context["form"] = form
    context["title"] = f"Create {model._meta.verbose_name.title()}"
    context["submit_text"] = f"Create {model._meta.verbose_name.title()}"

    return TemplateResponse(request, template_name, context)


def generic_update_view(
    request: WSGIRequest,
    pk: int,
    model: Model,
    form_class: Any,
    template_name: str = "laboratory/other/form.html",
    queryset: Optional[QuerySet] = None,
    extra_context: Optional[Dict[str, Any]] = None,
    success_url: Optional[str] = None,
) -> HttpResponse:
    """Generic update view for laboratory items."""
    # Get object
    if queryset is None:
        queryset = model.objects.all()
    item = get_object_or_404(queryset, pk=pk)

    # Handle form
    if request.method == "POST":
        form = form_class(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"{model._meta.verbose_name.title()} updated successfully!")
            return redirect(success_url or item.get_absolute_url())
        else:
            logger.error("Error creating %s: %s", model._meta.verbose_name, form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = form_class(instance=item)

    # Prepare context
    context = extra_context or {}
    if hasattr(item, "laboratory"):
        context = add_laboratory_context(context, item.laboratory)
    context = add_model_context(context, model)
    context["form"] = form
    context["object"] = item
    context["title"] = f"Update {model._meta.verbose_name.title()}"
    context["submit_text"] = f"Update {model._meta.verbose_name.title()}"

    return TemplateResponse(request, template_name, context)


# ExperimentalDevice Views


def device_list(request):
    """List all experimental devices."""
    return generic_list_view(
        request,
        ExperimentalDevice,
        queryset=ExperimentalDevice.objects.select_related("laboratory"),
        create_url_name="laboratory:device_create",
        update_url_name="laboratory:device_update",
    )


def device_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about an experimental device."""
    template = "laboratory/other/device_detail.html"
    context: Dict[str, Any] = {}

    # Get the device with related laboratory info
    device = get_object_or_404(ExperimentalDevice.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate efficiency metrics and thresholds
    power_per_memory = None
    if device.power_output and device.memory_capacity:
        try:
            # Convert power to watts and memory to gigabytes for consistent comparison
            power_watts = device.power_output.kilowatt.magnitude
            memory_gb = device.memory_capacity.quantity.to("gigabyte").magnitude
            power_per_memory = power_watts / memory_gb
        except Exception as e:
            logger.error("Error calculating power per memory: %s", e)

    # Calculate percentage values for progress bars
    power_percentage = 0
    if device.power_output:
        power_gw = device.power_output.quantity.to("gigawatt").magnitude
        power_percentage = min((power_gw / 1000) * 100, 100)  # Using 1000 GW as max

    quantum_percentage = 0
    if device.quantum_uncertainty:
        quantum_mev = device.quantum_uncertainty.quantity.to("meV").magnitude
        quantum_percentage = min((quantum_mev / 100) * 100, 100)  # Using 100 meV as max

    portal_percentage = 0
    if device.portal_diameter:
        portal_m = device.portal_diameter.meter.magnitude
        portal_percentage = min((portal_m / 10) * 100, 100)  # Using 10m as max

    # Get device status
    device_status = "stable"
    if device.power_output:
        power_gw = device.power_output.quantity.to("gigawatt").magnitude
        if power_gw > 1000:
            device_status = "danger"
        elif power_gw > 500:
            device_status = "warning"

    # Determine if device has dimensional manipulation capabilities
    is_dimensional = bool(
        device.portal_diameter
        or (device.quantum_uncertainty and device.quantum_uncertainty.quantity.to("meV").magnitude > 100)
    )

    # Organize measurement data for template
    measurements = {
        "power_output": {
            "value": device.power_output,
            "unit_choices": device._meta.get_field("power_output").unit_choices,
            "label": "Power Output",
            "show_conversions": True,
            "warning_threshold": "500 GW",
            "danger_threshold": "1000 GW",
        },
        "memory_capacity": {
            "value": device.memory_capacity,
            "unit_choices": device._meta.get_field("memory_capacity").unit_choices,
            "label": "Memory Capacity",
            "show_conversions": True,
        },
        "quantum_uncertainty": {
            "value": device.quantum_uncertainty,
            "unit_choices": device._meta.get_field("quantum_uncertainty").unit_choices,
            "label": "Quantum Uncertainty",
            "show_conversions": True,
            "warning_threshold": "50 meV",
            "danger_threshold": "100 meV",
        },
        "dimensional_wavelength": {
            "value": device.dimensional_wavelength,
            "unit_choices": device._meta.get_field("dimensional_wavelength").unit_choices,
            "label": "Dimensional Wavelength",
            "show_conversions": True,
        },
        "portal_diameter": {
            "value": device.portal_diameter,
            "unit_choices": device._meta.get_field("portal_diameter").unit_choices,
            "label": "Portal Diameter",
            "show_conversions": True,
            "warning_threshold": "5 m",
            "danger_threshold": "10 m",
        },
        "fuel_tank_capacity": {
            "value": device.fuel_tank_capacity,
            "unit_choices": device._meta.get_field("fuel_tank_capacity").unit_choices,
            "label": "Fuel Capacity",
            "show_conversions": True,
        },
    }

    context.update(
        {
            "device": device,
            "measurements": measurements,
            "device_status": device_status,
            "is_dimensional": is_dimensional,
            "power_per_memory": power_per_memory,
            "power_percentage": power_percentage,
            "quantum_percentage": quantum_percentage,
            "portal_percentage": portal_percentage,
        }
    )

    return TemplateResponse(request, template, context)


def device_create(request):
    """Create a new experimental device."""
    return generic_create_view(request, ExperimentalDevice, ExperimentalDeviceForm)


def device_update(request, pk):
    """Update an existing experimental device."""
    return generic_update_view(request, pk, ExperimentalDevice, ExperimentalDeviceForm)


# AnomalousSubstance Views


def substance_list(request):
    """List all anomalous substances."""
    return generic_list_view(
        request,
        AnomalousSubstance,
        queryset=AnomalousSubstance.objects.select_related("laboratory"),
        create_url_name="laboratory:substance_create",
        update_url_name="laboratory:substance_update",
    )


def substance_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about an anomalous substance."""
    template = "laboratory/other/substance_detail.html"
    context: Dict[str, Any] = {}

    # Get the substance with related laboratory info
    substance = get_object_or_404(
        AnomalousSubstance.objects.select_related("laboratory", "laboratory__universe"), pk=pk
    )

    # Calculate stability thresholds based on temperature and warping field
    stability_status = "stable"
    if substance.containment_temperature and substance.reality_warping_field:
        temp_k = substance.containment_temperature.quantity.to("kelvin").magnitude
        warping_mt = substance.reality_warping_field.quantity.to("millitesla").magnitude

        if temp_k > 1000 and warping_mt > 500:
            stability_status = "danger"
        elif temp_k > 500 or warping_mt > 250:
            stability_status = "warning"

    # Calculate percentage values for progress bars
    temp_percentage = 0
    if substance.containment_temperature:
        temp_k = substance.containment_temperature.quantity.to("kelvin").magnitude
        temp_percentage = min((temp_k / 2000) * 100, 100)  # Using 2000K as max

    warping_percentage = 0
    if substance.reality_warping_field:
        warping_mt = substance.reality_warping_field.quantity.to("millitesla").magnitude
        warping_percentage = min((warping_mt / 1000) * 100, 100)  # Using 1000mT as max

    volume_percentage = 0
    if substance.container_volume:
        volume_l = substance.container_volume.quantity.to("liter").magnitude
        volume_percentage = min((volume_l / 1000) * 100, 100)  # Using 1000L as max

    # Determine if substance has extreme properties
    is_extreme = bool(
        (substance.containment_temperature and substance.containment_temperature.quantity.to("kelvin").magnitude > 1000)
        or (
            substance.reality_warping_field
            and substance.reality_warping_field.quantity.to("millitesla").magnitude > 500
        )
    )

    # Organize measurement data for template
    measurements = {
        "containment_temperature": {
            "value": substance.containment_temperature,
            "unit_choices": substance._meta.get_field("containment_temperature").unit_choices,
            "label": "Containment Temperature",
            "show_conversions": True,
            "warning_threshold": "500 K",
            "danger_threshold": "1000 K",
        },
        "container_volume": {
            "value": substance.container_volume,
            "unit_choices": substance._meta.get_field("container_volume").unit_choices,
            "label": "Container Volume",
            "show_conversions": True,
        },
        "critical_mass": {
            "value": substance.critical_mass,
            "unit_choices": substance._meta.get_field("critical_mass").unit_choices,
            "label": "Critical Mass",
            "show_conversions": True,
        },
        "half_life": {
            "value": substance.half_life,
            "unit_choices": substance._meta.get_field("half_life").unit_choices,
            "label": "Half Life",
            "show_conversions": True,
        },
        "typical_shelf_life": {
            "value": substance.typical_shelf_life,
            "unit_choices": substance._meta.get_field("typical_shelf_life").unit_choices,
            "label": "Typical Shelf Life",
            "show_conversions": True,
        },
        "reality_warping_field": {
            "value": substance.reality_warping_field,
            "unit_choices": substance._meta.get_field("reality_warping_field").unit_choices,
            "label": "Reality Warping Field",
            "show_conversions": True,
            "warning_threshold": "250 mT",
            "danger_threshold": "500 mT",
        },
    }

    context.update(
        {
            "substance": substance,
            "measurements": measurements,
            "stability_status": stability_status,
            "is_extreme": is_extreme,
            "temp_percentage": temp_percentage,
            "warping_percentage": warping_percentage,
            "volume_percentage": volume_percentage,
        }
    )

    return TemplateResponse(request, template, context)


def substance_create(request):
    """Create a new anomalous substance."""
    return generic_create_view(request, AnomalousSubstance, AnomalousSubstanceForm)


def substance_update(request, pk):
    """Update an existing anomalous substance."""
    return generic_update_view(request, pk, AnomalousSubstance, AnomalousSubstanceForm)


# IncidentReport Views


def incident_list(request):
    """List all incident reports."""
    return generic_list_view(
        request,
        IncidentReport,
        queryset=IncidentReport.objects.select_related("laboratory"),
        create_url_name="laboratory:incident_create",
        update_url_name="laboratory:incident_update",
    )


def incident_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about an incident report."""
    template = "laboratory/other/incident_detail.html"
    context: Dict[str, Any] = {}

    # Get the incident with related laboratory info
    incident = get_object_or_404(IncidentReport.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate incident status based on severity and affected area
    incident_status = "stable"
    if incident.severity >= 4:
        incident_status = "danger"
    elif incident.severity >= 3:
        incident_status = "warning"

    # Calculate percentage values for progress bars
    radius_percentage = 0
    if incident.affected_radius:
        radius_km = incident.affected_radius.quantity.to("kilometer").magnitude
        radius_percentage = min((radius_km / 100) * 100, 100)  # Using 100km as max

    temporal_percentage = 0
    if incident.temporal_displacement:
        years = abs(incident.temporal_displacement.quantity.to("year").magnitude)
        temporal_percentage = min((years / 100) * 100, 100)  # Using 100 years as max

    # Determine if incident has major temporal effects
    has_temporal_effects = bool(
        incident.temporal_displacement and abs(incident.temporal_displacement.quantity.to("year").magnitude) > 1
    )

    # Calculate time since incident
    time_since = None
    if incident.timestamp:
        time_since = timezone.now() - incident.timestamp

    # Get dimensional stability at time of incident
    stability_change = None
    if incident.severity >= 3:
        # For severe incidents, check if dimensional stability was affected
        try:
            # This assumes you have historical stability data - adjust as needed
            stability_change = incident.laboratory.dimensional_stability - 100
        except Exception as e:
            logger.error("Error calculating stability change: %s", e)

    # Organize measurement data for template
    measurements = {
        "affected_radius": {
            "value": incident.affected_radius,
            "unit_choices": incident._meta.get_field("affected_radius").unit_choices,
            "label": "Affected Radius",
            "show_conversions": True,
            "warning_threshold": "50 km",
            "danger_threshold": "100 km",
        },
        "temporal_displacement": {
            "value": incident.temporal_displacement,
            "unit_choices": incident._meta.get_field("temporal_displacement").unit_choices,
            "label": "Temporal Displacement",
            "show_conversions": True,
            "warning_threshold": "1 year",
            "danger_threshold": "10 years",
        },
    }

    context.update(
        {
            "incident": incident,
            "measurements": measurements,
            "incident_status": incident_status,
            "has_temporal_effects": has_temporal_effects,
            "radius_percentage": radius_percentage,
            "temporal_percentage": temporal_percentage,
            "time_since": time_since,
            "stability_change": stability_change,
        }
    )

    return TemplateResponse(request, template, context)


def incident_create(request):
    """Create a new incident report."""
    return generic_create_view(request, IncidentReport, IncidentReportForm)


def incident_update(request, pk):
    """Update an existing incident report."""
    return generic_update_view(request, pk, IncidentReport, IncidentReportForm)


# SafetyProtocol Views


def protocol_list(request):
    """List all safety protocols."""
    return generic_list_view(
        request,
        SafetyProtocol,
        queryset=SafetyProtocol.objects.select_related("laboratory"),
        create_url_name="laboratory:protocol_create",
        update_url_name="laboratory:protocol_update",
    )


def protocol_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about a safety protocol."""
    template = "laboratory/other/protocol_detail.html"
    context: Dict[str, Any] = {}

    # Get the protocol with related laboratory info
    protocol = get_object_or_404(SafetyProtocol.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate protocol status based on field strength and resonance
    protocol_status = "stable"
    if protocol.containment_field_strength and protocol.shield_frequency:
        # Convert to base units for comparison
        field_mv_m = protocol.containment_field_strength.quantity.to("megavolt_per_meter").magnitude
        freq_ghz = protocol.shield_frequency.quantity.to("gigahertz").magnitude

        # Check resonance ratio
        resonance_ratio = field_mv_m / freq_ghz
        if 0.8 < resonance_ratio < 1.2:
            protocol_status = "danger"  # Near resonance
        elif 0.6 < resonance_ratio < 1.4:
            protocol_status = "warning"  # Approaching resonance

    # Calculate percentage values for progress bars
    field_percentage = 0
    if protocol.containment_field_strength:
        mv_m = protocol.containment_field_strength.quantity.to("megavolt_per_meter").magnitude
        field_percentage = min((mv_m / 100) * 100, 100)  # Using 100 MV/m as max

    frequency_percentage = 0
    if protocol.shield_frequency:
        ghz = protocol.shield_frequency.quantity.to("gigahertz").magnitude
        frequency_percentage = min((ghz / 1000) * 100, 100)  # Using 1000 GHz as max

    # Calculate time since last update
    time_since_update = None
    if protocol.last_updated:
        time_since_update = timezone.now() - protocol.last_updated

    # Determine if protocol needs review
    needs_review = bool(
        protocol_status == "warning"
        or protocol_status == "danger"
        or (time_since_update and time_since_update.days > 30)  # Monthly review
    )

    # Calculate resonance risk
    resonance_risk = None
    if protocol.containment_field_strength and protocol.shield_frequency:
        try:
            field_mv_m = protocol.containment_field_strength.quantity.to("megavolt_per_meter").magnitude
            freq_ghz = protocol.shield_frequency.quantity.to("gigahertz").magnitude
            ratio = field_mv_m / freq_ghz
            # Calculate how close to resonance (1.0) the ratio is
            resonance_risk = max(0, 100 - abs(1 - ratio) * 100)
        except Exception as e:
            logger.error("Error calculating resonance risk: %s", e)

    # Organize measurement data for template
    measurements = {
        "containment_field_strength": {
            "value": protocol.containment_field_strength,
            "unit_choices": protocol._meta.get_field("containment_field_strength").unit_choices,
            "label": "Containment Field Strength",
            "show_conversions": True,
            "warning_threshold": "50 MV/m",
            "danger_threshold": "100 MV/m",
        },
        "shield_frequency": {
            "value": protocol.shield_frequency,
            "unit_choices": protocol._meta.get_field("shield_frequency").unit_choices,
            "label": "Shield Frequency",
            "show_conversions": True,
            "warning_threshold": "500 GHz",
            "danger_threshold": "1000 GHz",
        },
    }

    context.update(
        {
            "protocol": protocol,
            "measurements": measurements,
            "protocol_status": protocol_status,
            "needs_review": needs_review,
            "field_percentage": field_percentage,
            "frequency_percentage": frequency_percentage,
            "time_since_update": time_since_update,
            "resonance_risk": resonance_risk,
        }
    )

    return TemplateResponse(request, template, context)


def protocol_create(request):
    """Create a new safety protocol."""
    return generic_create_view(request, SafetyProtocol, SafetyProtocolForm)


def protocol_update(request, pk):
    """Update an existing safety protocol."""
    return generic_update_view(request, pk, SafetyProtocol, SafetyProtocolForm)


# ExperimentSubject Views


def subject_list(request):
    """List all experiment subjects."""
    return generic_list_view(
        request,
        ExperimentSubject,
        queryset=ExperimentSubject.objects.select_related("laboratory"),
        create_url_name="laboratory:subject_create",
        update_url_name="laboratory:subject_update",
    )


def subject_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about an experiment subject."""
    template = "laboratory/other/subject_detail.html"
    context: Dict[str, Any] = {}

    # Get the subject with related laboratory info
    subject = get_object_or_404(ExperimentSubject.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate status based on IQ and processing power
    subject_status = "stable"
    if subject.intelligence_quotient > 200:
        subject_status = "warning"  # High intelligence may indicate developing sentience
    if subject.processing_speed and subject.processing_speed.quantity.to("GIPS").magnitude > 1000:
        subject_status = "danger"  # Extremely high processing power

    # Calculate percentage values for progress bars
    iq_percentage = min((subject.intelligence_quotient / 300) * 100, 100)  # Using 300 as max IQ

    processing_percentage = 0
    if subject.processing_speed:
        gips = subject.processing_speed.quantity.to("GIPS").magnitude
        processing_percentage = min((gips / 300) * 100, 100)  # Using 300 GIPS as max

    power_percentage = 0
    if subject.power_consumption:
        watts = subject.power_consumption.quantity.to("watt").magnitude
        power_percentage = min((watts / 1500) * 100, 100)  # Using 1500W as max

    # Calculate efficiency metrics
    processing_per_watt = None
    if subject.processing_speed and subject.power_consumption:
        try:
            # Convert to consistent units (MIPS per watt)
            processing_mips = subject.processing_speed.quantity.to("MIPS").magnitude
            power_watts = subject.power_consumption.quantity.to("watt").magnitude
            processing_per_watt = processing_mips / power_watts
        except Exception as e:
            logger.error("Error calculating processing per watt: %s", e)

    # Determine if subject shows signs of advanced capabilities
    is_advanced = bool(
        subject.intelligence_quotient > 150
        or (subject.processing_speed and subject.processing_speed.quantity.to("GIPS").magnitude > 500)
    )

    # Calculate time since creation
    time_active = None
    if subject.creation_date:
        time_active = timezone.now() - subject.creation_date

    # Organize measurement data for template
    measurements = {
        "processing_speed": {
            "value": subject.processing_speed,
            "unit_choices": subject._meta.get_field("processing_speed").unit_choices,
            "label": "Processing Speed",
            "show_conversions": True,
            "warning_threshold": "500 GIPS",
            "danger_threshold": "1000 GIPS",
        },
        "power_consumption": {
            "value": subject.power_consumption,
            "unit_choices": subject._meta.get_field("power_consumption").unit_choices,
            "label": "Power Consumption",
            "show_conversions": True,
            "warning_threshold": "500 W",
            "danger_threshold": "1000 W",
        },
    }

    context.update(
        {
            "subject": subject,
            "measurements": measurements,
            "subject_status": subject_status,
            "is_advanced": is_advanced,
            "iq_percentage": iq_percentage,
            "processing_percentage": processing_percentage,
            "power_percentage": power_percentage,
            "processing_per_watt": processing_per_watt,
            "time_active": time_active,
        }
    )

    return TemplateResponse(request, template, context)


def subject_create(request):
    """Create a new experiment subject."""
    return generic_create_view(request, ExperimentSubject, ExperimentSubjectForm)


def subject_update(request, pk):
    """Update an existing experiment subject."""
    return generic_update_view(request, pk, ExperimentSubject, ExperimentSubjectForm)


# DimensionalRift Views


def rift_list(request):
    """List all dimensional rifts."""
    return generic_list_view(
        request,
        DimensionalRift,
        queryset=DimensionalRift.objects.select_related("laboratory"),
        create_url_name="laboratory:rift_create",
        update_url_name="laboratory:rift_update",
    )


def rift_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about a dimensional rift."""
    template = "laboratory/other/rift_detail.html"
    context: Dict[str, Any] = {}

    # Get the rift with related laboratory info
    rift = get_object_or_404(DimensionalRift.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate rift status based on stability and energy
    rift_status = "stable" if rift.is_stable else "warning"
    if rift.energy_output and rift.energy_output.quantity.to("teraelectronvolt").magnitude > 1000:
        rift_status = "danger"

    # Calculate percentage values for progress bars
    diameter_percentage = 0
    if rift.diameter:
        meters = rift.diameter.quantity.to("meter").magnitude
        diameter_percentage = min((meters / 100) * 100, 100)  # Using 100m as max

    energy_percentage = 0
    if rift.energy_output:
        tev = rift.energy_output.quantity.to("teraelectronvolt").magnitude
        energy_percentage = min((tev / 2000) * 100, 100)  # Using 2000 TeV as max

    curvature_percentage = 0
    if rift.spacetime_curvature:
        curvature = rift.spacetime_curvature.quantity.to("inverse_meter_squared").magnitude
        curvature_percentage = min((curvature / 1000) * 100, 100)  # Using 1000 m⁻² as max

    # Calculate time since detection
    time_since = None
    if rift.detected_at:
        time_since = timezone.now() - rift.detected_at

    # Determine if rift is critically unstable
    is_critical = bool(
        not rift.is_stable
        and (
            (rift.diameter and rift.diameter.quantity.to("meter").magnitude > 50)
            or (rift.energy_output and rift.energy_output.quantity.to("teraelectronvolt").magnitude > 500)
            or (
                rift.spacetime_curvature
                and rift.spacetime_curvature.quantity.to("inverse_meter_squared").magnitude > 500
            )
        )
    )

    # Calculate stability risk
    stability_risk = 0
    if rift.diameter and rift.energy_output and rift.spacetime_curvature:
        try:
            # Normalize each metric to 0-1 scale and average
            d_norm = min(rift.diameter.meter.magnitude / 100, 1)
            e_norm = min(rift.energy_output.teraelectronvolt.magnitude / 2000, 1)
            c_norm = min(rift.spacetime_curvature.inverse_meter_squared.magnitude / 1000, 1)
            stability_risk = ((d_norm + e_norm + c_norm) / 3) * 100
        except Exception as e:
            logger.error("Error calculating stability risk: %s", e)

    # Organize measurement data for template
    measurements = {
        "diameter": {
            "value": rift.diameter,
            "unit_choices": rift._meta.get_field("diameter").unit_choices,
            "label": "Rift Diameter",
            "show_conversions": True,
            "warning_threshold": "50 m",
            "danger_threshold": "100 m",
        },
        "energy_output": {
            "value": rift.energy_output,
            "unit_choices": rift._meta.get_field("energy_output").unit_choices,
            "label": "Energy Output",
            "show_conversions": True,
            "warning_threshold": "500 TeV",
            "danger_threshold": "1000 TeV",
        },
        "spacetime_curvature": {
            "value": rift.spacetime_curvature,
            "unit_choices": rift._meta.get_field("spacetime_curvature").unit_choices,
            "label": "Spacetime Curvature",
            "show_conversions": True,
            "warning_threshold": "500 m⁻²",
            "danger_threshold": "1000 m⁻²",
        },
    }

    context.update(
        {
            "rift": rift,
            "measurements": measurements,
            "rift_status": rift_status,
            "is_critical": is_critical,
            "diameter_percentage": diameter_percentage,
            "energy_percentage": energy_percentage,
            "curvature_percentage": curvature_percentage,
            "time_since": time_since,
            "stability_risk": stability_risk,
        }
    )

    return TemplateResponse(request, template, context)


def rift_create(request):
    """Create a new dimensional rift."""
    return generic_create_view(request, DimensionalRift, DimensionalRiftForm)


def rift_update(request, pk):
    """Update an existing dimensional rift."""
    return generic_update_view(request, pk, DimensionalRift, DimensionalRiftForm)


# EnergyReading Views


def energy_list(request):
    """List all energy readings."""
    return generic_list_view(
        request,
        EnergyReading,
        queryset=EnergyReading.objects.select_related("laboratory"),
        create_url_name="laboratory:energy_create",
        update_url_name="laboratory:energy_update",
    )


def energy_detail(request, pk: int) -> TemplateResponse:
    """Display detailed information about an energy reading."""
    template = "laboratory/other/energy_detail.html"
    context: Dict[str, Any] = {}

    # Get the reading with related laboratory info
    reading = get_object_or_404(EnergyReading.objects.select_related("laboratory", "laboratory__universe"), pk=pk)

    # Calculate reading status based on radiation and energy levels
    reading_status = "stable"
    if reading.background_radiation and reading.tachyon_flux:
        # Convert to base units for comparison
        radiation_sv = reading.background_radiation.quantity.to("sievert_per_hour").magnitude
        tachyons_cps = reading.tachyon_flux.quantity.to("counts_per_second").magnitude

        if radiation_sv > 0.1 and tachyons_cps > 1000000:
            reading_status = "danger"  # High radiation with excessive tachyons
        elif radiation_sv > 0.05 or tachyons_cps > 500000:
            reading_status = "warning"

    # Calculate percentage values for progress bars
    radiation_percentage = 0
    if reading.background_radiation:
        sv_h = reading.background_radiation.quantity.to("sievert_per_hour").magnitude
        radiation_percentage = min((sv_h / Decimal("0.2")) * 100, 100)  # Using 0.2 Sv/h as max

    tachyon_percentage = 0
    if reading.tachyon_flux:
        cps = reading.tachyon_flux.quantity.to("counts_per_second").magnitude
        tachyon_percentage = min((cps / 2000000) * 100, 100)  # Using 2M counts/s as max

    energy_percentage = 0
    if reading.dark_energy_density:
        mj_m3 = reading.dark_energy_density.quantity.to("megajoule_per_m3").magnitude
        energy_percentage = min((mj_m3 / 2000) * 100, 100)  # Using 2000 MJ/m³ as max

    # Calculate time since reading
    time_since = None
    if reading.timestamp:
        time_since = timezone.now() - reading.timestamp

    # Determine if reading shows anomalous values
    is_anomalous = bool(
        (reading.background_radiation and reading.background_radiation.quantity.to("sievert_per_hour").magnitude > 0.1)
        or (reading.tachyon_flux and reading.tachyon_flux.quantity.to("counts_per_second").magnitude > 1000000)
        or (
            reading.dark_energy_density and reading.dark_energy_density.quantity.to("megajoule_per_m3").magnitude > 1000
        )
    )

    # Calculate containment breach risk
    breach_risk = None
    if all([reading.background_radiation, reading.tachyon_flux, reading.dark_energy_density]):
        try:
            # Normalize each reading to 0-1 scale and calculate weighted average
            rad_norm = min(reading.background_radiation.quantity.to("sievert_per_hour").magnitude / Decimal("0.2"), 1)
            tach_norm = min(reading.tachyon_flux.quantity.to("counts_per_second").magnitude / Decimal("2000000"), 1)
            energy_norm = min(
                reading.dark_energy_density.quantity.to("megajoule_per_m3").magnitude / Decimal("2000"), 1
            )

            # Weight tachyon flux higher as it's more indicative of containment issues
            breach_risk = (
                (rad_norm * Decimal("0.3")) + (tach_norm * Decimal("0.5")) + (energy_norm * Decimal("0.2"))
            ) * Decimal("100")
        except Exception as e:
            logger.error("Error calculating breach risk: %s", e)

    # Organize measurement data for template
    measurements = {
        "background_radiation": {
            "value": reading.background_radiation,
            "unit_choices": reading._meta.get_field("background_radiation").unit_choices,
            "label": "Background Radiation",
            "show_conversions": True,
            "warning_threshold": "0.05 Sv/h",
            "danger_threshold": "0.1 Sv/h",
        },
        "tachyon_flux": {
            "value": reading.tachyon_flux,
            "unit_choices": reading._meta.get_field("tachyon_flux").unit_choices,
            "label": "Tachyon Flux",
            "show_conversions": True,
            "warning_threshold": "500000 counts/s",
            "danger_threshold": "1000000 counts/s",
        },
        "dark_energy_density": {
            "value": reading.dark_energy_density,
            "unit_choices": reading._meta.get_field("dark_energy_density").unit_choices,
            "label": "Dark Energy Density",
            "show_conversions": True,
            "warning_threshold": "1000 MJ/m³",
            "danger_threshold": "2000 MJ/m³",
        },
    }

    context.update(
        {
            "reading": reading,
            "measurements": measurements,
            "reading_status": reading_status,
            "is_anomalous": is_anomalous,
            "radiation_percentage": radiation_percentage,
            "tachyon_percentage": tachyon_percentage,
            "energy_percentage": energy_percentage,
            "time_since": time_since,
            "breach_risk": breach_risk,
        }
    )

    return TemplateResponse(request, template, context)


def energy_create(request):
    """Create a new energy reading."""
    return generic_create_view(request, EnergyReading, EnergyReadingForm)


def energy_update(request, pk):
    """Update an existing energy reading."""
    return generic_update_view(request, pk, EnergyReading, EnergyReadingForm)
