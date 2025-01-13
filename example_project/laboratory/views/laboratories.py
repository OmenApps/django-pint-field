"""Views for managing laboratories."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintSum

from ..forms import LaboratoryForm
from ..models import AnomalousSubstance
from ..models import ExperimentalDevice
from ..models import IncidentReport
from ..models import Laboratory
from ..models import Universe


@login_required
def laboratory_list(request):
    """Display list of all laboratories across universes."""
    template = "laboratory/laboratories/laboratory_list.html"
    context = {}

    # Get all labs with their universe info
    laboratories = Laboratory.objects.select_related("universe").all()

    # Calculate some stats for each lab
    stats = {}
    for lab in laboratories:
        stats[lab.id] = {
            "device_count": ExperimentalDevice.objects.filter(laboratory=lab).count(),
            "substance_count": AnomalousSubstance.objects.filter(laboratory=lab).count(),
            "avg_power_output": ExperimentalDevice.objects.filter(laboratory=lab).aggregate(
                PintAvg("power_output", output_unit="GW")
            )["power_output__pintavg"],
        }

    context["laboratories"] = laboratories
    context["stats"] = stats
    return TemplateResponse(request, template, context)


@login_required
def laboratory_detail(request, pk):
    """Display comprehensive overview of a laboratory combining dashboard and details."""
    template = "laboratory/laboratories/laboratory_detail.html"
    context = {}

    # Get the laboratory with related info
    laboratory = get_object_or_404(Laboratory.objects.select_related("universe"), pk=pk)

    # Get all related devices
    devices = ExperimentalDevice.objects.filter(laboratory=laboratory)

    # Get all related substances
    substances = AnomalousSubstance.objects.filter(laboratory=laboratory)

    # Get all related incidents
    incidents = IncidentReport.objects.filter(laboratory=laboratory)

    # Calculate basic lab statistics
    stats = {
        "total_devices": devices.count(),
        "total_substances": substances.count(),
        "avg_power_output": devices.aggregate(PintAvg("power_output", output_unit="GW"))["power_output__pintavg"],
        "total_power": devices.aggregate(total_power=PintSum("power_output"))["total_power"],
        "avg_quantum_uncertainty": devices.aggregate(PintAvg("quantum_uncertainty"))["quantum_uncertainty__pintavg"],
        "portal_count": devices.exclude(portal_diameter__isnull=True).count(),
    }

    # Calculate substance statistics
    substance_stats = {
        "total_mass": substances.aggregate(total_mass=PintSum("critical_mass"))["total_mass"],
        "avg_containment_temp": substances.aggregate(PintAvg("containment_temperature"))[
            "containment_temperature__pintavg"
        ],
        "avg_warping_field": substances.aggregate(PintAvg("reality_warping_field"))["reality_warping_field__pintavg"],
        "total_volume": substances.aggregate(total_volume=PintSum("container_volume", output_unit="L"))["total_volume"],
    }

    # Calculate high-risk metrics
    high_risk_metrics = {
        "dangerous_devices": devices.filter(power_output__gt=1000).count(),  # Devices with power output > 1000 GW
        "unstable_substances": substances.filter(
            reality_warping_field__gt=500  # Substances with warping field > 500 mT
        ).count(),
        "dimensional_portals": devices.exclude(portal_diameter__isnull=True)
        .filter(portal_diameter__gt=10)  # Portals larger than 10m
        .count(),
    }

    # Calculate time-based metrics
    current_time = timezone.now()
    time_metrics = {
        "days_since_established": (
            (current_time.date() - laboratory.established_date).days if laboratory.established_date else None
        ),
        "avg_device_power_last_week": devices.filter(power_output__isnull=False).aggregate(
            avg_power=PintAvg("power_output")
        )["avg_power"],
        "avg_stability_trend": None,  # Would need historical data for this
    }

    context.update(
        {
            "laboratory": laboratory,
            "devices": devices,
            "substances": substances,
            "incidents": incidents,
            "stats": stats,
            "substance_stats": substance_stats,
            "high_risk_metrics": high_risk_metrics,
            "time_metrics": time_metrics,
            # Keep both short and full lists for flexibility
            "recent_devices": devices.order_by("-id")[:5],  # Latest 5 devices
            "recent_substances": substances.order_by("-id")[:5],  # Latest 5 substances
        }
    )

    return TemplateResponse(request, template, context)


@login_required
def laboratory_create(request):
    """Create a new laboratory."""
    template = "laboratory/laboratories/laboratory_form.html"
    context = {}

    # Handle pre-selected universe from query params
    universe_id = request.GET.get("universe")
    initial = {}
    if universe_id:
        try:
            universe = Universe.objects.get(id=universe_id)
            initial["universe"] = universe
        except Universe.DoesNotExist:
            pass

    if request.method == "POST":
        form = LaboratoryForm(request.POST)
        if form.is_valid():
            laboratory = form.save()
            messages.success(request, f"Laboratory '{laboratory.name}' created successfully!")
            return redirect("laboratory:laboratory_detail", pk=laboratory.pk)
    else:
        form = LaboratoryForm(initial=initial)

    context.update({"form": form, "title": "Create New Laboratory", "submit_text": "Create Laboratory"})
    return TemplateResponse(request, template, context)


@login_required
def laboratory_update(request, pk):
    """Update an existing laboratory."""
    template = "laboratory/laboratories/laboratory_form.html"
    context = {}

    laboratory = get_object_or_404(Laboratory, pk=pk)

    if request.method == "POST":
        form = LaboratoryForm(request.POST, instance=laboratory)
        if form.is_valid():
            laboratory = form.save()
            messages.success(request, f"Laboratory '{laboratory.name}' updated successfully!")
            return redirect("laboratory:laboratory_detail", pk=laboratory.pk)
    else:
        form = LaboratoryForm(instance=laboratory)

    context.update(
        {
            "form": form,
            "laboratory": laboratory,
            "title": f"Update Laboratory: {laboratory.name}",
            "submit_text": "Update Laboratory",
        }
    )
    return TemplateResponse(request, template, context)
