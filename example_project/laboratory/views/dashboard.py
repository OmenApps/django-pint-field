"""Views for the main dashboard and command center."""

import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils import timezone

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintSum
from example_project.laboratory.models import AnomalousSubstance
from example_project.laboratory.models import DimensionalRift
from example_project.laboratory.models import EnergyReading
from example_project.laboratory.models import ExperimentalDevice
from example_project.laboratory.models import IncidentReport
from example_project.laboratory.models import Laboratory
from example_project.laboratory.models import SafetyProtocol
from example_project.laboratory.models import Universe


logger = logging.getLogger(__name__)


class GeoJSONEncoder(DjangoJSONEncoder):
    """Custom JSON encoder for GeoJSON data."""

    def default(self, obj):
        if isinstance(obj, (Decimal, float)):
            return float(obj)
        return super().default(obj)


def main_dashboard(request):
    """Display the main command center dashboard with critical metrics."""
    template = "laboratory/dashboard/main_dashboard.html"
    context = {}

    # Get time thresholds
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)

    # Universe statistics
    universes = Universe.objects.all()
    universe_stats = {
        "total": universes.count(),
        "labs_per_universe": Laboratory.objects.count() / max(universes.count(), 1),
    }

    # Laboratory statistics
    laboratories = Laboratory.objects.all()
    lab_stats = {
        "total": laboratories.count(),
        "evil_labs": laboratories.filter(is_evil=True).count(),
        "high_risk": laboratories.filter(containment_level__gte=4).count(),
        "avg_stability": laboratories.aggregate(Avg("dimensional_stability"))["dimensional_stability__avg"] or 0,
        "critical_stability": laboratories.filter(dimensional_stability__lt=25).count(),
    }

    # Device statistics
    devices = ExperimentalDevice.objects.all()
    device_stats = {
        "total": devices.count(),
        "total_power": devices.aggregate(PintSum("power_output", output_unit="GW"))["power_output__pintsum"],
        "avg_uncertainty": devices.aggregate(PintAvg("quantum_uncertainty", output_unit="meV"))[
            "quantum_uncertainty__pintavg"
        ],
    }

    # Substance statistics
    substances = AnomalousSubstance.objects.all()
    substance_stats = {
        "total": substances.count(),
        "avg_temp": substances.aggregate(PintAvg("containment_temperature", output_unit="K"))[
            "containment_temperature__pintavg"
        ],
        "total_mass": substances.aggregate(PintSum("critical_mass", output_unit="g"))["critical_mass__pintsum"],
        "high_warping": substances.filter(reality_warping_field__gt=Decimal("1000")).count(),  # >1000 mT
    }

    # Recent incidents
    recent_incidents = IncidentReport.objects.filter(timestamp__gte=last_week).order_by("-timestamp")
    incident_stats = {
        "last_24h": recent_incidents.count(),
        "severe": recent_incidents.filter(severity__gte=4).count(),
        "by_severity": recent_incidents.values("severity").annotate(count=Count("id")).order_by("severity"),
    }

    # Active dimensional rifts
    active_rifts = DimensionalRift.objects.filter(is_stable=False, detected_at__gte=last_week).order_by("-detected_at")
    rift_stats = {
        "total_active": active_rifts.count(),
        "avg_diameter": active_rifts.aggregate(PintAvg("diameter", output_unit="m"))["diameter__pintavg"],
        "total_energy": active_rifts.aggregate(PintSum("energy_output", output_unit="TeV"))["energy_output__pintsum"],
    }

    # Energy readings
    recent_readings = EnergyReading.objects.filter(timestamp__gte=last_24h).order_by("-timestamp")
    energy_stats = {
        "avg_radiation": recent_readings.aggregate(PintAvg("background_radiation", output_unit="uSv_per_h"))[
            "background_radiation__pintavg"
        ],
        "avg_tachyons": recent_readings.aggregate(PintAvg("tachyon_flux", output_unit="kilocounts_per_second"))[
            "tachyon_flux__pintavg"
        ],
        "dark_energy": recent_readings.aggregate(PintAvg("dark_energy_density", output_unit="megajoule_per_m3"))[
            "dark_energy_density__pintavg"
        ],
    }

    # Critical alerts
    critical_alerts = []

    # Check for dangerous stability levels
    critical_labs = laboratories.filter(
        Q(dimensional_stability__lt=25)  # Very low stability
        | Q(containment_level__gte=4, dimensional_stability__lt=50)  # High risk + low stability
    )
    for lab in critical_labs:
        critical_alerts.append(
            {
                "type": "stability",
                "severity": "danger" if lab.dimensional_stability < 25 else "warning",
                "message": f"Critical stability in {lab.name}: {lab.dimensional_stability}%",
                "lab": lab,
            }
        )

    # Check for high warping fields
    dangerous_substances = substances.filter(reality_warping_field__gt=Decimal("1000"))  # >1000 mT
    for substance in dangerous_substances:
        critical_alerts.append(
            {
                "type": "warping",
                "severity": "warning",
                "message": f"High reality warping detected from {substance.name}",
                "lab": substance.laboratory,
            }
        )

    # Check for active unstable rifts
    unstable_rifts = active_rifts.filter(
        Q(diameter__gt=Decimal("100")) | Q(energy_output__gt=Decimal("1000"))  # >100m diameter  # >1000 TeV
    )
    for rift in unstable_rifts:
        critical_alerts.append(
            {
                "type": "rift",
                "severity": "danger",
                "message": f"Unstable dimensional rift detected at {rift.laboratory.name}",
                "lab": rift.laboratory,
            }
        )

    context.update(
        {
            "universe_stats": universe_stats,
            "lab_stats": lab_stats,
            "device_stats": device_stats,
            "substance_stats": substance_stats,
            "incident_stats": incident_stats,
            "rift_stats": rift_stats,
            "energy_stats": energy_stats,
            "recent_incidents": recent_incidents[:5],  # Last 5 incidents
            "active_rifts": active_rifts[:5],  # Top 5 active rifts
            "critical_alerts": critical_alerts,
        }
    )

    return TemplateResponse(request, template, context)


def system_status(request):
    """Display current system status and health metrics."""
    template = "laboratory/dashboard/system_status.html"
    context = {}

    # Get current timestamp
    now = timezone.now()
    last_24h = now - timedelta(hours=24)

    # Get all active laboratories
    laboratories = Laboratory.objects.all()

    # Calculate overall system health
    total_labs = laboratories.count()
    stable_labs = laboratories.filter(dimensional_stability__gte=75).count()
    system_health = (stable_labs / total_labs * 100) if total_labs > 0 else 0

    # Get recent energy readings
    recent_readings = EnergyReading.objects.filter(timestamp__gte=last_24h).order_by("-timestamp")

    # Get active safety protocols
    active_protocols = SafetyProtocol.objects.filter(laboratory__dimensional_stability__lt=75).select_related(
        "laboratory"
    )

    context.update(
        {
            "system_health": system_health,
            "total_labs": total_labs,
            "stable_labs": stable_labs,
            "recent_readings": recent_readings[:10],  # Last 10 readings
            "active_protocols": active_protocols,
        }
    )

    return TemplateResponse(request, template, context)


def dimensional_stability(request):
    """Monitor dimensional stability across all laboratories."""
    template = "laboratory/dashboard/dimensional_stability.html"
    context = {}

    # Get all laboratories ordered by stability
    laboratories = Laboratory.objects.all().order_by("dimensional_stability")

    # Group labs by stability range
    stability_ranges = {
        "critical": laboratories.filter(dimensional_stability__lt=25),
        "unstable": laboratories.filter(dimensional_stability__range=(25, 50)),
        "fluctuating": laboratories.filter(dimensional_stability__range=(50, 75)),
        "stable": laboratories.filter(dimensional_stability__gte=75),
    }

    # Get dimensional rifts
    active_rifts = DimensionalRift.objects.filter(is_stable=False).select_related("laboratory")

    # Create a dictionary to store curvature values
    curvature_values = {}

    # Calculate average curvature by stability range
    for range_name, labs in stability_ranges.items():
        rifts = active_rifts.filter(laboratory__in=labs)
        avg_curvature = rifts.aggregate(PintAvg("spacetime_curvature", output_unit="inverse_meter_squared"))[
            "spacetime_curvature__pintavg"
        ]
        logger.debug("Average curvature for %s: %s", range_name, avg_curvature)
        curvature_values[f"{range_name}_curvature"] = avg_curvature
    logger.debug("Curvature values: %s", curvature_values)

    # Update the stability_ranges dictionary with curvature values
    stability_ranges.update(curvature_values)

    context.update(
        {
            "stability_ranges": stability_ranges,
            "active_rifts": active_rifts,
        }
    )

    return TemplateResponse(request, template, context)


def global_incident_map(request):
    """Display a global map of laboratory incidents and anomalies."""
    template = "laboratory/dashboard/global_incident_map.html"

    # Get time thresholds
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_week = now - timedelta(days=7)

    # Get laboratories with their metrics
    laboratories = Laboratory.objects.annotate(
        recent_incidents=Count("incidentreport", filter=Q(incidentreport__timestamp__gte=last_24h)),
        recent_rifts=Count(
            "dimensionalrift", filter=Q(dimensionalrift__is_stable=False, dimensionalrift__detected_at__gte=last_24h)
        ),
        total_incidents=Count("incidentreport", filter=Q(incidentreport__timestamp__gte=last_week)),
        total_rifts=Count(
            "dimensionalrift", filter=Q(dimensionalrift__is_stable=False, dimensionalrift__detected_at__gte=last_week)
        ),
        avg_rift_energy=PintAvg(
            "dimensionalrift__energy_output",
            filter=Q(dimensionalrift__is_stable=False, dimensionalrift__detected_at__gte=last_week),
            output_unit="TeV",
        ),
    ).select_related("universe")

    # Get recent incidents and rifts
    recent_incidents = (
        IncidentReport.objects.filter(timestamp__gte=last_week).select_related("laboratory").order_by("-timestamp")
    )

    very_recent_incidents = recent_incidents.filter(timestamp__gte=last_24h)

    active_rifts = (
        DimensionalRift.objects.filter(is_stable=False, detected_at__gte=last_week)
        .select_related("laboratory")
        .order_by("-detected_at")
    )

    new_rifts = active_rifts.filter(detected_at__gte=last_24h)

    # Get laboratories with critical stability
    critical_labs = laboratories.filter(
        Q(dimensional_stability__lt=25)  # Very low stability
        | Q(containment_level__gte=4, dimensional_stability__lt=50)  # High risk + low stability
    )

    # Prepare GeoJSON feature collections
    lab_features = []
    for lab in laboratories:
        if lab.total_incidents > 0 or lab.total_rifts > 0 or lab.dimensional_stability < 50:
            # Determine marker type and styling
            if lab.dimensional_stability < 25:
                marker_type = "critical"
                marker_color = "#ff0033"
            elif lab.recent_incidents > 0 or lab.recent_rifts > 0:
                marker_type = "recent"
                marker_color = "#ff7700"
            elif lab.total_incidents > 0:
                marker_type = "incident"
                marker_color = "#ffff00"
            else:
                marker_type = "warning"
                marker_color = "#ffaa00"

            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lab.location_lng), float(lab.location_lat)]},
                "properties": {
                    "id": lab.id,
                    "name": lab.name,
                    "universe": lab.universe.name,
                    "stability": float(lab.dimensional_stability),
                    "recent_incidents": lab.recent_incidents,
                    "total_incidents": lab.total_incidents,
                    "recent_rifts": lab.recent_rifts,
                    "total_rifts": lab.total_rifts,
                    "marker_type": marker_type,
                    "marker_color": marker_color,
                    "containment_level": lab.containment_level,
                    "is_evil": bool(lab.is_evil),  # Convert to native Python bool
                },
            }
            lab_features.append(feature)

    geojson = {"type": "FeatureCollection", "features": lab_features}

    context = {
        "geojson": json.dumps(geojson, cls=GeoJSONEncoder),  # Use custom encoder
        "recent_incidents": recent_incidents[:10],
        "very_recent_incidents": very_recent_incidents,
        "active_rifts": active_rifts[:5],
        "new_rifts": new_rifts,
        "critical_labs": critical_labs[:5],
        "total_incidents": recent_incidents.count(),
        "recent_incident_count": very_recent_incidents.count(),
        "total_rifts": active_rifts.count(),
        "recent_rift_count": new_rifts.count(),
        "total_critical": critical_labs.count(),
        "last_update": now,
    }

    return TemplateResponse(request, template, context)
