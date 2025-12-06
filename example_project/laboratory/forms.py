"""Forms for the laboratory management system."""

from django import forms

from example_project.laboratory.models import AnomalousSubstance
from example_project.laboratory.models import DimensionalRift
from example_project.laboratory.models import EnergyReading
from example_project.laboratory.models import ExperimentalDevice
from example_project.laboratory.models import IncidentReport
from example_project.laboratory.models import Laboratory
from example_project.laboratory.models import SafetyProtocol
from example_project.laboratory.models import ExperimentSubject
from example_project.laboratory.models import Universe


class UniverseForm(forms.ModelForm):
    """Form for creating and updating Universes."""

    class Meta:
        """Meta options for UniverseForm."""

        model = Universe
        fields = [
            "name",
            "description",
            "year_introduced",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 3},
            ),
            "year_introduced": forms.NumberInput(
                attrs={"min": 1800, "max": 2100},
            ),
        }
        help_texts = {
            "year_introduced": "The year this fictional universe was first introduced",
        }


class LaboratoryForm(forms.ModelForm):
    """Form for creating and updating Laboratories."""

    class Meta:
        """Meta options for LaboratoryForm."""

        model = Laboratory
        fields = [
            "name",
            "universe",
            "location",
            "location_lat",
            "location_lng",
            "established_date",
            "containment_level",
            "dimensional_stability",
            "is_evil",
        ]
        widgets = {
            "established_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "dimensional_stability": forms.NumberInput(
                attrs={
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                    "class": "form-control",
                }
            ),
            "containment_level": forms.Select(attrs={"class": "form-control"}),
            "is_evil": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "location_lat": forms.NumberInput(
                attrs={
                    "min": "-90",
                    "max": "90",
                    "step": "0.000001",
                    "class": "form-control",
                }
            ),
            "location_lng": forms.NumberInput(
                attrs={
                    "min": "-180",
                    "max": "180",
                    "step": "0.000001",
                    "class": "form-control",
                }
            ),
        }
        help_texts = {
            "established_date": "When this laboratory was first established",
            "dimensional_stability": "Current stability of local spacetime (0-100%)",
            "containment_level": "Required safety protocols and containment measures",
            "is_evil": "Check if this laboratory has evil intentions or regularly creates supervillains",
            "location_lat": "Latitude coordinates (e.g., 40.7128)",
            "location_lng": "Longitude coordinates (e.g., -74.0060)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.CheckboxInput):
                self.fields[field].widget.attrs["class"] = "form-control"

    def clean_dimensional_stability(self):
        """Validate dimensional stability is within bounds."""
        stability = self.cleaned_data["dimensional_stability"]
        if stability < 0 or stability > 100:
            raise forms.ValidationError("Dimensional stability must be between 0 and 100%")
        return stability

    def clean(self):
        """Custom validation for the form."""
        cleaned_data = super().clean()

        # If containment level is high but stability is too high, warn about it
        containment_level = cleaned_data.get("containment_level")
        stability = cleaned_data.get("dimensional_stability")

        if containment_level and stability:
            if containment_level >= 4 and stability > 75:
                raise forms.ValidationError(
                    "High containment level laboratories typically have lower dimensional stability"
                )

            # Evil labs should have lower stability
            is_evil = cleaned_data.get("is_evil")
            if is_evil and stability > 80:
                raise forms.ValidationError("Evil laboratories typically have poor dimensional stability")

        return cleaned_data


class ExperimentalDeviceForm(forms.ModelForm):
    """Form for creating and updating experimental devices."""

    class Meta:
        """Meta options for ExperimentalDeviceForm."""

        model = ExperimentalDevice
        fields = [
            "name",
            "laboratory",
            "fuel_tank_capacity",
            "memory_capacity",
            "power_output",
            "quantum_uncertainty",
            "dimensional_wavelength",
            "portal_diameter",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "power_output": "Power output of the device",
            "quantum_uncertainty": "Quantum uncertainty level in measurements",
            "portal_diameter": "Diameter of any dimensional portals created (if applicable)",
        }

    def clean(self):
        """Custom validation for experimental devices."""
        cleaned_data = super().clean()
        power_output = cleaned_data.get("power_output")
        portal_diameter = cleaned_data.get("portal_diameter")

        if power_output and portal_diameter:
            # Convert to common units for comparison
            power_gw = power_output.to("gigawatt").magnitude
            diameter_m = portal_diameter.to("meter").magnitude

            # Safety check - high power with large portals is dangerous
            if power_gw > 1000 and diameter_m > 10:
                raise forms.ValidationError(
                    "Power output over 1000 GW with portals larger than 10m " "creates dangerous spacetime instability."
                )

        return cleaned_data


class AnomalousSubstanceForm(forms.ModelForm):
    """Form for creating and updating anomalous substances."""

    class Meta:
        """Meta options for AnomalousSubstanceForm."""

        model = AnomalousSubstance
        fields = [
            "name",
            "laboratory",
            "containment_temperature",
            "container_volume",
            "critical_mass",
            "half_life",
            "typical_shelf_life",
            "reality_warping_field",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "containment_temperature": "Required temperature for safe storage",
            "critical_mass": "Mass at which anomalous effects become unstable",
            "reality_warping_field": "Strength of local reality distortion field",
        }

    def clean(self):
        """Custom validation for anomalous substances."""
        cleaned_data = super().clean()
        temp = cleaned_data.get("containment_temperature")
        warping = cleaned_data.get("reality_warping_field")

        if temp and warping:
            # Convert to common units
            temp_k = temp.to("kelvin").magnitude
            warping_mt = warping.to("millitesla").magnitude

            # Check for dangerous combinations
            if temp_k > 1000 and warping_mt > 500:
                raise forms.ValidationError(
                    "High temperatures (> 1,000 K) combined with strong reality warping "
                    "fields (> 500 mT) can cause dimensional instability."
                )

        return cleaned_data


class ExperimentSubjectForm(forms.ModelForm):
    """Form for creating and updating experiment subjects."""

    class Meta:
        """Meta options for ExperimentSubjectForm."""

        model = ExperimentSubject
        fields = [
            "identifier",
            "laboratory",
            "creation_date",
            "intelligence_quotient",
            "processing_speed",
            "power_consumption",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "creation_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "intelligence_quotient": forms.NumberInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "intelligence_quotient": "Measured IQ score",
            "processing_speed": "Neural/computational processing speed",
            "power_consumption": "Average power consumption",
        }

    def clean_intelligence_quotient(self):
        """Validate intelligence quotient is within reasonable bounds."""
        iq = self.cleaned_data.get("intelligence_quotient")
        if iq and (iq < 0 or iq > 300):
            raise forms.ValidationError(
                "Intelligence quotient must be between 0 and 300. Higher values are not survivable."
            )
        return iq


class IncidentReportForm(forms.ModelForm):
    """Form for creating and updating incident reports."""

    class Meta:
        """Meta options for IncidentReportForm."""

        model = IncidentReport
        fields = [
            "laboratory",
            "timestamp",
            "description",
            "severity",
            "affected_radius",
            "temporal_displacement",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "timestamp": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "severity": forms.Select(attrs={"class": "form-select"}),
        }
        help_texts = {
            "severity": "Impact level of the incident",
            "affected_radius": "Radius of affected area",
            "temporal_displacement": "Time distortion caused by the incident",
        }

    def clean(self):
        """Validate incident report details."""
        cleaned_data = super().clean()
        severity = cleaned_data.get("severity")
        radius = cleaned_data.get("affected_radius")
        displacement = cleaned_data.get("temporal_displacement")

        if severity and radius:
            # Convert radius to kilometers for comparison
            radius_km = radius.to("kilometer").magnitude

            # Check if radius matches severity level
            if severity < 3 and radius_km > 10:
                raise forms.ValidationError("Low severity incidents should not affect such a large area.")
            elif severity >= 4 and radius_km < 1:
                raise forms.ValidationError("High severity incidents typically affect larger areas.")

        if severity and displacement:
            # Convert displacement to years for comparison
            displacement_years = displacement.to("year").magnitude

            # Check if temporal displacement matches severity
            if severity < 4 and abs(displacement_years) > 1:
                raise forms.ValidationError("Significant temporal displacement should be marked as high severity.")

        return cleaned_data


class DimensionalRiftForm(forms.ModelForm):
    """Form for creating and updating dimensional rifts."""

    class Meta:
        """Meta options for DimensionalRiftForm."""

        model = DimensionalRift
        fields = [
            "laboratory",
            "detected_at",
            "is_stable",
            "diameter",
            "energy_output",
            "spacetime_curvature",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "detected_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_stable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "is_stable": "Whether the rift has stabilized",
            "diameter": "Current diameter of the rift",
            "energy_output": "Energy being emitted by the rift",
            "spacetime_curvature": "Local spacetime curvature around the rift",
        }

    def clean(self):
        """Validate dimensional rift measurements."""
        cleaned_data = super().clean()
        is_stable = cleaned_data.get("is_stable")
        diameter = cleaned_data.get("diameter")
        energy = cleaned_data.get("energy_output")
        curvature = cleaned_data.get("spacetime_curvature")

        if all([is_stable, diameter, energy, curvature]):
            # Convert to common units for comparison
            diameter_m = diameter.to("meter").magnitude
            energy_tev = energy.to("teraelectronvolt").magnitude
            curvature_m = curvature.to("inverse_meter_squared").magnitude

            # Check stability criteria
            if is_stable:
                if diameter_m > 100:
                    raise forms.ValidationError("Rifts larger than 100m cannot maintain stability.")
                if energy_tev > 1000:
                    raise forms.ValidationError("Rifts emitting over 1000 TeV cannot be considered stable.")
                if curvature_m > 1000:
                    raise forms.ValidationError("Extreme spacetime curvature indicates instability.")

        return cleaned_data


class SafetyProtocolForm(forms.ModelForm):
    """Form for creating and updating safety protocols."""

    class Meta:
        """Meta options for SafetyProtocolForm."""

        model = SafetyProtocol
        fields = [
            "laboratory",
            "name",
            "description",
            "containment_field_strength",
            "shield_frequency",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        help_texts = {
            "containment_field_strength": "Strength of containment field",
            "shield_frequency": "Frequency of shield harmonics",
        }

    def clean(self):
        """Validate safety protocol settings."""
        cleaned_data = super().clean()
        field_strength = cleaned_data.get("containment_field_strength")
        frequency = cleaned_data.get("shield_frequency")

        if field_strength and frequency:
            # Convert to base units
            strength_mv_m = field_strength.to("megavolt_per_meter").magnitude
            freq_ghz = frequency.to("gigahertz").magnitude

            # Check for resonance issues
            if 0.8 < (strength_mv_m / freq_ghz) < 1.2:
                raise forms.ValidationError(
                    "Field strength and shield frequency are too close to "
                    "resonance. This could cause containment failure."
                )

        return cleaned_data


class EnergyReadingForm(forms.ModelForm):
    """Form for creating and updating energy readings."""

    class Meta:
        """Meta options for EnergyReadingForm."""

        model = EnergyReading
        fields = [
            "laboratory",
            "timestamp",
            "background_radiation",
            "tachyon_flux",
            "dark_energy_density",
        ]
        widgets = {
            "laboratory": forms.Select(attrs={"class": "form-select"}),
            "timestamp": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }
        help_texts = {
            "background_radiation": "Ambient radiation level",
            "tachyon_flux": "Measured tachyonic particle flux",
            "dark_energy_density": "Local dark energy density",
        }

    def clean(self):
        """Validate energy readings."""
        cleaned_data = super().clean()
        radiation = cleaned_data.get("background_radiation")
        tachyons = cleaned_data.get("tachyon_flux")
        dark_energy = cleaned_data.get("dark_energy_density")

        if all([radiation, tachyons, dark_energy]):
            # Convert to common units
            radiation_sv = radiation.to("sievert_per_hour").magnitude
            tachyons_cps = tachyons.to("counts_per_second").magnitude
            energy_mj = dark_energy.to("megajoule_per_m3").magnitude

            # Check for dangerous energy levels
            if radiation_sv > 0.1 and tachyons_cps > 1000000:
                raise forms.ValidationError(
                    "High radiation (> 0.1 sV) with excessive tachyon flux (> 1 Mcps) indicates imminent "
                    "containment breach."
                )
            if energy_mj > 1000 and tachyons_cps > 1000000:
                raise forms.ValidationError(
                    "Dark energy density (> 1 kj) and tachyon flux (> 1 Mcps) levels suggest dimensional instability."
                )

        return cleaned_data
