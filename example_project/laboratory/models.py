"""Models for the Fictional Laboratory Management Network."""

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from django_pint_field.models import DecimalPintField
from django_pint_field.models import IntegerPintField


User = get_user_model()


class Universe(models.Model):
    """Represents different fictional universes (e.g. Marvel, Resident Evil, etc.)."""

    name = models.CharField(max_length=200)
    description = models.TextField()
    year_introduced = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Laboratory(models.Model):
    """Represents a fictional laboratory facility."""

    name = models.CharField(max_length=200)
    universe = models.ForeignKey(Universe, on_delete=models.CASCADE)
    location = models.CharField(max_length=200)
    established_date = models.DateField(null=True, blank=True)

    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Latitude",
        help_text="Latitude coordinates (e.g., 40.7128)",
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Longitude",
        help_text="Longitude coordinates (e.g., -74.0060)",
    )

    class ContainmentLevel(models.IntegerChoices):
        """Choices for containment levels."""

        MINIMAL_RISK = 1, "Minimal Risk - Safe for Interns"
        MODERATE_RISK = 2, "Moderate Risk - Mad Science Basics"
        HIGH_RISK = 3, "High Risk - Full Mad Science"
        EXTREME_RISK = 4, "Extreme Risk - Reality Bending"
        ULTIMATE_RISK = 5, "Ultimate Risk - Timeline Altering"

    containment_level = models.IntegerField(
        choices=ContainmentLevel.choices,
        default=ContainmentLevel.MODERATE_RISK,
    )
    dimensional_stability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage stability of local spacetime",
    )
    is_evil = models.BooleanField(
        default=False,
        help_text="Does this lab regularly create supervillains?",
    )

    class Meta:
        """Meta options for the Laboratory model."""

        verbose_name_plural = "Laboratories"

    def __str__(self):
        return f"{self.name} ({self.universe.name})"

    @property
    def status(self):
        """Get the current status of the laboratory."""
        if self.dimensional_stability >= 75:
            return "stable"
        elif self.dimensional_stability >= 50:
            return "warning"
        return "danger"


class ExperimentalDevice(models.Model):
    """Track information about experimental devices/machines."""

    name = models.CharField(max_length=200)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)

    fuel_tank_capacity = IntegerPintField(
        default_unit=["L", "liter"],
        unit_choices=[
            # ["L", "liter"],
            ["gal", "gallon"],
            ["m³", "cubic_meter"],
            "shot",
            "hogshead",
        ],
        help_text="Total fuel tank capacity in whole units",
    )

    memory_capacity = IntegerPintField(
        default_unit=["GB", "gigabyte"],
        unit_choices=[
            ["GB", "gigabyte"],
            ["TB", "terabyte"],
            ["PB", "petabyte"],
        ],
        help_text="Memory storage in whole units",
    )

    power_output = DecimalPintField(
        default_unit=["GW", "gigawatt"],  # Perfect for Doc Brown's flux capacitor
        unit_choices=[
            # ["GW", "gigawatt"],
            ["MW", "megawatt"],
            ["kW", "kilowatt"],
            ["W", "watt"],
        ],
    )

    quantum_uncertainty = DecimalPintField(
        default_unit=["meV", "meV"],
        unit_choices=[
            # rydberg:
            ("Ry", "rydberg"),
            ["Eh", "hartree"],
            ("meV", "meV"),
            ("µeV", "ueV"),
            ["Ton of TNT", "ton_TNT"],
            ("Ton of Oil Equivalent", "toe"),
        ],
    )

    dimensional_wavelength = DecimalPintField(
        default_unit=("Å", "angstrom"),
        unit_choices=(
            ("Å", "angstrom"),
            ("nm", "nanometer"),
            ("µm", "micrometer"),
        ),
    )

    portal_diameter = DecimalPintField(
        default_unit="meter",
        unit_choices=[
            "meter",
            "centimeter",
            "foot",
        ],
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get the absolute URL for the device detail view."""
        return reverse("laboratory:device_detail", kwargs={"pk": self.pk})


class AnomalousSubstance(models.Model):
    """Track information about mysterious substances."""

    name = models.CharField(max_length=200)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)

    containment_temperature = DecimalPintField(
        default_unit=["K", "kelvin"],
        unit_choices=(
            ["K", "kelvin"],
            ["°C", "degC"],
            ["°F", "degF"],
        ),
    )

    container_volume = IntegerPintField(
        default_unit=["mL", "milliliter"],
        unit_choices=[
            ["mL", "milliliter"],
            ["L", "liter"],
            "gallon",
        ],
        help_text="Standard container volume in whole units",
    )

    critical_mass = DecimalPintField(
        default_unit=["µg", "microgram"],
        unit_choices=(
            ("µg", "microgram"),
            ("mg", "milligram"),
            ("g", "gram"),
        ),
    )

    half_life = DecimalPintField(
        default_unit=["day", "day"],
        unit_choices=[
            # "day",
            "hour",
            "minute",
        ],
    )

    typical_shelf_life = IntegerPintField(
        default_unit="day",
        unit_choices=(
            ["day", "day"],
            ["mo", "month"],
            ["yr", "year"],
        ),
        help_text="Shelf life in whole time units",
    )

    reality_warping_field = DecimalPintField(
        default_unit=("mT", "millitesla"),
        unit_choices=[
            ("mT", "millitesla"),
            ("µT", "microtesla"),
            ("nT", "nanotesla"),
            ("gigagamma", "gigagamma"),
        ],
        help_text="Typical field strength of any reality warping effect",
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get the absolute URL for the substance detail view."""
        return reverse("laboratory:substance_detail", kwargs={"pk": self.pk})


class TestSubject(models.Model):
    """Track information about test subjects (clones, robots, etc.)."""

    identifier = models.CharField(max_length=50)
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    creation_date = models.DateTimeField()

    intelligence_quotient = models.PositiveSmallIntegerField(help_text="Measured in standard IQ units")

    processing_speed = DecimalPintField(
        default_unit=["MIPS", "MIPS"],
        unit_choices=[
            ["MIPS", "MIPS"],
            ["GIPS", "GIPS"],
            ["TIPS", "TIPS"],
        ],
    )

    power_consumption = DecimalPintField(
        default_unit=("W", "watt"),
        unit_choices=[
            ("W", "watt"),
            ["kW", "kilowatt"],
            ["mW", "milliwatt"],
        ],
    )

    def __str__(self):
        return self.identifier

    def get_absolute_url(self):
        """Get the absolute URL for the subject detail view."""
        return reverse("laboratory:subject_detail", kwargs={"pk": self.pk})


class IncidentReport(models.Model):
    """Track laboratory incidents (containment breaches, etc.)."""

    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    description = models.TextField()

    class IncidentSeverity(models.IntegerChoices):
        """Choices for incident severity."""

        MINOR = 1, "Minor - Easily Contained"
        MODERATE = 2, "Moderate - Local Effects"
        MAJOR = 3, "Major - City-wide Impact"
        SEVERE = 4, "Severe - Global Implications"
        CATASTROPHIC = 5, "Catastrophic - Reality Breach"

    severity = models.IntegerField(
        choices=IncidentSeverity.choices,
        default=IncidentSeverity.MODERATE,
    )

    affected_radius = DecimalPintField(
        default_unit=["km", "kilometer"],
        unit_choices=[
            ["km", "kilometer"],
            ["m", "meter"],
            ["mi", "mile"],
        ],
    )

    temporal_displacement = DecimalPintField(
        default_unit=["y", "year"],
        unit_choices=[
            ["y", "year"],
            ["mo", "month"],
            ["d", "day"],
        ],
    )

    def __str__(self):
        return f"{self.timestamp} - {self.description}"

    def get_absolute_url(self):
        """Get the absolute URL for the incident detail view."""
        return reverse("laboratory:incident_detail", kwargs={"pk": self.pk})


class DimensionalRift(models.Model):
    """Track interdimensional portals and rifts."""

    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    detected_at = models.DateTimeField()
    is_stable = models.BooleanField(default=False)

    diameter = DecimalPintField(
        default_unit=["m", "meter"],
        unit_choices=[
            ["m", "meter"],
            ["km", "kilometer"],
            ["ft", "foot"],
        ],
    )

    energy_output = DecimalPintField(
        default_unit=["TeV", "teraelectronvolt"],
        unit_choices=(
            ("TeV", "teraelectronvolt"),
            ("GeV", "gigaelectronvolt"),
            ("MeV", "megaelectronvolt"),
        ),
    )

    spacetime_curvature = DecimalPintField(
        default_unit=["m⁻2", "inverse_meter_squared"],
        unit_choices=[
            ("m⁻2", "inverse_meter_squared"),
            ["km⁻2", "inverse_kilometer_squared"],
        ],
    )

    def __str__(self):
        return f"{self.detected_at}"

    def get_absolute_url(self):
        """Get the absolute URL for the rift detail view."""
        return reverse("laboratory:rift_detail", kwargs={"pk": self.pk})


class SafetyProtocol(models.Model):
    """Track safety protocols and containment procedures."""

    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    containment_field_strength = DecimalPintField(
        default_unit=("MV/m", "megavolt_per_meter"),
        unit_choices=[
            ["MV/m", "megavolt_per_meter"],
            ["kV/m", "kilovolt_per_meter"],
            ["V/m", "volt_per_meter"],
        ],
    )

    shield_frequency = DecimalPintField(
        default_unit=["GHz", "gigahertz"],
        unit_choices=[
            ["THz", "terahertz"],
            ["GHz", "gigahertz"],
            ["MHz", "megahertz"],
            ["kHz", "kilohertz"],
            ["Hz", "hertz"],
        ],
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get the absolute URL for the protocol detail view."""
        return reverse("laboratory:protocol_detail", kwargs={"pk": self.pk})


class EnergyReading(models.Model):
    """Track various energy readings and measurements."""

    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    background_radiation = DecimalPintField(
        default_unit=["µSv/h", "microsievert_per_hour"],
        unit_choices=[
            ["µSv/h", "microsievert_per_hour"],
            ["mSv/h", "millisievert_per_hour"],
            ["Sv/h", "sievert_per_hour"],
        ],
    )

    tachyon_flux = DecimalPintField(
        default_unit=["particles/s", "counts_per_second"],
        unit_choices=[
            ["particles/s", "counts_per_second"],
            ["kparticles/s", "kilocounts_per_second"],
            ["Mparticles/s", "megacounts_per_second"],
        ],
    )

    dark_energy_density = DecimalPintField(
        default_unit=["J/m³", "joule_per_cubic_meter"],
        unit_choices=[
            ["J/m³", "joule_per_cubic_meter"],
            ["kJ/m³", "kilojoule_per_cubic_meter"],
            ["MJ/m³", "megajoule_per_cubic_meter"],
        ],
    )

    def __str__(self):
        return f"{self.timestamp}"

    def get_absolute_url(self):
        """Get the absolute URL for the energy reading detail view."""
        return reverse("laboratory:energy_detail", kwargs={"pk": self.pk})
