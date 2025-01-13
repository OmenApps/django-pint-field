"""Custom management command to populate the database with fictional laboratory data."""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from example_project.laboratory.models import AnomalousSubstance
from example_project.laboratory.models import DimensionalRift
from example_project.laboratory.models import EnergyReading
from example_project.laboratory.models import ExperimentalDevice
from example_project.laboratory.models import IncidentReport
from example_project.laboratory.models import Laboratory
from example_project.laboratory.models import SafetyProtocol
from example_project.laboratory.models import TestSubject
from example_project.laboratory.models import Universe


class Command(BaseCommand):
    """Populate the database with fictional laboratory data."""

    help = "Populates the database with fictional laboratories and related data"

    def handle(self, *args, **options):
        self.stdout.write("Removing any existing content...")
        # Clear existing data
        ExperimentalDevice.objects.all().delete()
        AnomalousSubstance.objects.all().delete()
        TestSubject.objects.all().delete()
        IncidentReport.objects.all().delete()
        DimensionalRift.objects.all().delete()
        SafetyProtocol.objects.all().delete()
        EnergyReading.objects.all().delete()
        Laboratory.objects.all().delete()
        Universe.objects.all().delete()

        self.stdout.write("Removals complete.\n\n")

        self.stdout.write("Creating fictional universes...")

        # Create universes
        universes = {
            "DC": self.create_universe(
                "DC Universe",
                "A universe of superheroes and advanced science",
                1935,
            ),
            "Resident Evil": self.create_universe(
                "Resident Evil",
                "A world plagued by bioweapons and corporate evil",
                1996,
            ),
            "Half-Life": self.create_universe(
                "Half-Life",
                "A world where a physics experiment gone wrong leads to an alien invasion",
                1998,
            ),
            "Portal": self.create_universe(
                "Portal",
                "A world of advanced AI and physics-defying technology",
                2007,
            ),
            "Back to the Future": self.create_universe(
                "Back to the Future",
                "A world where time travel is possible through scientific innovation",
                1985,
            ),
            "Dexter's Laboratory": self.create_universe(
                "Dexter's Laboratory",
                "A world where a boy genius conducts secret experiments",
                1996,
            ),
            "Marvel": self.create_universe(
                "Marvel Universe (Earth-616)",
                "The primary continuity of Marvel Comics",
                1961,
            ),
            "SCP": self.create_universe(
                "SCP Foundation",
                "A world where a secret organization contains anomalous entities",
                2008,
            ),
            "Lost": self.create_universe(
                "Lost",
                "A mysterious island with strange scientific facilities",
                2004,
            ),
            "RoboCop": self.create_universe(
                "RoboCop",
                "A cyberpunk future where corporations control law enforcement",
                1987,
            ),
            "Frankenstein": self.create_universe(
                "Frankenstein",
                "The classic tale of scientific hubris",
                1818,
            ),
            "Stranger Things": self.create_universe(
                "Stranger Things",
                "A world of supernatural mysteries and government experiments",
                2016,
            ),
        }

        # Define laboratory data
        laboratories = [
            {
                "name": "Ararat Corporation Arctic Research Facility",
                "universe": universes["Marvel"],
                "location": "Arctic Circle",
                "established_date": "1982-12-15",
                "containment_level": 4,
                "dimensional_stability": Decimal("58.9"),
                "is_evil": True,
                "location_lat": Decimal("78.0000"),  # Approximate Arctic Circle latitude
                "location_lng": Decimal("15.0000"),  # Approximate Arctic Circle longitude
            },
            {
                "name": "Arklay Laboratory",
                "universe": universes["Resident Evil"],
                "location": "Arklay Mountains",
                "established_date": "1962-06-15",
                "containment_level": 5,
                "dimensional_stability": Decimal("82.3"),
                "is_evil": True,
                "location_lat": Decimal("35.0000"),  # Approximate Arklay Mountains (fictional, based on Japan)
                "location_lng": Decimal("138.0000"),
            },
            {
                "name": "Aperture Science Enrichment Center",
                "universe": universes["Portal"],
                "location": "Upper Michigan",
                "established_date": "1943-10-01",
                "containment_level": 4,
                "dimensional_stability": Decimal("72.8"),
                "is_evil": True,
                "location_lat": Decimal("46.5000"),  # Upper Michigan coordinates
                "location_lng": Decimal("-87.5000"),
            },
            {
                "name": "Black Mesa Research Facility",
                "universe": universes["Half-Life"],
                "location": "New Mexico",
                "established_date": "1955-08-20",
                "containment_level": 4,
                "dimensional_stability": Decimal("45.2"),
                "is_evil": False,
                "location_lat": Decimal("34.4048"),  # New Mexico coordinates
                "location_lng": Decimal("-106.9056"),
            },
            {
                "name": "Borealis Research Facility",
                "universe": universes["Half-Life"],
                "location": "Arctic Circle",
                "established_date": "1985-03-10",
                "containment_level": 4,
                "dimensional_stability": Decimal("50.1"),
                "is_evil": False,
                "location_lat": Decimal("78.0000"),  # Approximate Arctic Circle latitude
                "location_lng": Decimal("15.0000"),
            },
            {
                "name": "C.S.A. Advanced Technology Research Facility",
                "universe": universes["Marvel"],
                "location": "Portland, OR",
                "established_date": "1988-03-22",
                "containment_level": 3,
                "dimensional_stability": Decimal("92.5"),
                "is_evil": False,
                "location_lat": Decimal("45.5051"),  # Portland, OR coordinates
                "location_lng": Decimal("-122.6750"),
            },
            {
                "name": "Cord Castle Laboratory",
                "universe": universes["Marvel"],
                "location": "Long Island, NY",
                "established_date": "1969-09-30",
                "containment_level": 3,
                "dimensional_stability": Decimal("73.7"),
                "is_evil": False,
                "location_lat": Decimal("40.7891"),  # Long Island, NY coordinates
                "location_lng": Decimal("-73.1348"),
            },
            {
                "name": "Damocles Research Facility",
                "universe": universes["Marvel"],
                "location": "New Mexico",
                "established_date": "1971-07-04",
                "containment_level": 4,
                "dimensional_stability": Decimal("79.8"),
                "is_evil": True,
                "location_lat": Decimal("34.4048"),  # New Mexico coordinates
                "location_lng": Decimal("-106.9056"),
            },
            {
                "name": "Darkmoor Energy Research Centre",
                "universe": universes["Marvel"],
                "location": "England",
                "established_date": "1967-11-11",
                "containment_level": 4,
                "dimensional_stability": Decimal("62.3"),
                "is_evil": True,
                "location_lat": Decimal("51.5074"),  # England coordinates (London as reference)
                "location_lng": Decimal("-0.1278"),
            },
            {
                "name": "Department of Energy Facility",
                "universe": universes["Stranger Things"],
                "location": "Hawkins, Indiana",
                "established_date": "1983-11-01",
                "containment_level": 4,
                "dimensional_stability": Decimal("40.2"),
                "is_evil": True,
                "location_lat": Decimal("39.7684"),  # Indiana coordinates (Indianapolis as reference)
                "location_lng": Decimal("-86.1581"),
            },
            {
                "name": "Dexter's Laboratory",
                "universe": universes["Dexter's Laboratory"],
                "location": "Genius Grove",
                "established_date": "1996-04-28",
                "containment_level": 2,
                "dimensional_stability": Decimal("95.0"),
                "is_evil": False,
                "location_lat": Decimal("34.0522"),  # Genius Grove (fictional, based on Los Angeles)
                "location_lng": Decimal("-118.2437"),
            },
            {
                "name": "Doctor Brown's Lab",
                "universe": universes["Back to the Future"],
                "location": "Hill Valley, California",
                "established_date": "1955-11-05",
                "containment_level": 3,
                "dimensional_stability": Decimal("65.4"),
                "is_evil": False,
                "location_lat": Decimal("38.5816"),  # Hill Valley (fictional, based on Northern California)
                "location_lng": Decimal("-121.4944"),
            },
            {
                "name": "Dr. Connors' Laboratory",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1963-11-01",
                "containment_level": 3,
                "dimensional_stability": Decimal("55.9"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Frankenstein's Laboratory",
                "universe": universes["Frankenstein"],
                "location": "Ingolstadt, Bavaria",
                "established_date": "1792-11-30",
                "containment_level": 4,
                "dimensional_stability": Decimal("61.3"),
                "is_evil": False,
                "location_lat": Decimal("48.7667"),  # Ingolstadt, Bavaria coordinates
                "location_lng": Decimal("11.4333"),
            },
            {
                "name": "Genetech Science Facility",
                "universe": universes["Marvel"],
                "location": "Islip, NY",
                "established_date": "1978-02-14",
                "containment_level": 3,
                "dimensional_stability": Decimal("89.1"),
                "is_evil": False,
                "location_lat": Decimal("40.7298"),  # Islip, NY coordinates
                "location_lng": Decimal("-73.2104"),
            },
            {
                "name": "Hammond Labs",
                "universe": universes["Marvel"],
                "location": "Springdale, CT",
                "established_date": "1973-05-07",
                "containment_level": 3,
                "dimensional_stability": Decimal("98.2"),
                "is_evil": False,
                "location_lat": Decimal("41.9165"),  # Springdale, CT coordinates
                "location_lng": Decimal("-73.4540"),
            },
            {
                "name": "Hawkins National Laboratory",
                "universe": universes["Stranger Things"],
                "location": "Hawkins, Indiana",
                "established_date": "1979-05-15",
                "containment_level": 5,
                "dimensional_stability": Decimal("35.7"),
                "is_evil": True,
                "location_lat": Decimal("39.7684"),  # Indiana coordinates (Indianapolis as reference)
                "location_lng": Decimal("-86.1581"),
            },
            {
                "name": "Horizon Labs",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "2010-05-12",
                "containment_level": 4,
                "dimensional_stability": Decimal("91.2"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Hydra Laboratory 107",
                "universe": universes["Marvel"],
                "location": "Newark, NJ",
                "established_date": "1965-08-19",
                "containment_level": 4,
                "dimensional_stability": Decimal("75.6"),
                "is_evil": True,
                "location_lat": Decimal("40.7357"),  # Newark, NJ coordinates
                "location_lng": Decimal("-74.1724"),
            },
            {
                "name": "Hydra Laboratory 119",
                "universe": universes["Marvel"],
                "location": "Liberty Island, NY",
                "established_date": "1966-01-23",
                "containment_level": 4,
                "dimensional_stability": Decimal("53.4"),
                "is_evil": True,
                "location_lat": Decimal("40.6892"),  # Liberty Island, NY coordinates
                "location_lng": Decimal("-74.0445"),
            },
            {
                "name": "Institute of Seismoharmonic Research",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1975-06-18",
                "containment_level": 3,
                "dimensional_stability": Decimal("37.2"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Lab Discovera",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1989-11-03",
                "containment_level": 3,
                "dimensional_stability": Decimal("91.5"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Latverian Research Institute",
                "universe": universes["Marvel"],
                "location": "Latveria",
                "established_date": "1965-12-25",
                "containment_level": 5,
                "dimensional_stability": Decimal("20.5"),
                "is_evil": True,
                "location_lat": Decimal("46.1512"),  # Latveria (fictional, based on Eastern Europe)
                "location_lng": Decimal("14.9955"),
            },
            {
                "name": "LexCorp Labs",
                "universe": universes["DC"],
                "location": "Metropolis",
                "established_date": "1985-09-20",
                "containment_level": 4,
                "dimensional_stability": Decimal("74.3"),
                "is_evil": True,
                "location_lat": Decimal("40.7128"),  # Metropolis (fictional, based on New York City)
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Moon Girl's Secret Laboratory",
                "universe": universes["Marvel"],
                "location": "Lower East Side, Manhattan",
                "established_date": "2015-01-15",
                "containment_level": 2,
                "dimensional_stability": Decimal("97.5"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Lower East Side, Manhattan coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Morder Research Centre",
                "universe": universes["Marvel"],
                "location": "England",
                "established_date": "1970-10-31",
                "containment_level": 3,
                "dimensional_stability": Decimal("86.5"),
                "is_evil": False,
                "location_lat": Decimal("51.5074"),  # England coordinates (London as reference)
                "location_lng": Decimal("-0.1278"),
            },
            {
                "name": "OCP Bioengineering Lab",
                "universe": universes["RoboCop"],
                "location": "Detroit, Michigan",
                "established_date": "1988-02-14",
                "containment_level": 4,
                "dimensional_stability": Decimal("88.7"),
                "is_evil": True,
                "location_lat": Decimal("42.3314"),  # Detroit, Michigan coordinates
                "location_lng": Decimal("-83.0458"),
            },
            {
                "name": "OCP Delta City Research Facility",
                "universe": universes["RoboCop"],
                "location": "Delta City, Michigan",
                "established_date": "1990-03-15",
                "containment_level": 3,
                "dimensional_stability": Decimal("59.4"),
                "is_evil": True,
                "location_lat": Decimal("42.3314"),  # Delta City (fictional, based on Detroit)
                "location_lng": Decimal("-83.0458"),
            },
            {
                "name": "Omni Consumer Products Lab",
                "universe": universes["RoboCop"],
                "location": "Detroit, Michigan",
                "established_date": "1986-12-01",
                "containment_level": 3,
                "dimensional_stability": Decimal("92.1"),
                "is_evil": True,
                "location_lat": Decimal("42.3314"),  # Detroit, Michigan coordinates
                "location_lng": Decimal("-83.0458"),
            },
            {
                "name": "Omnitek Laboratories",
                "universe": universes["Marvel"],
                "location": "Lawton, OK",
                "established_date": "1981-04-01",
                "containment_level": 3,
                "dimensional_stability": Decimal("90.8"),
                "is_evil": False,
                "location_lat": Decimal("34.6036"),  # Lawton, OK coordinates
                "location_lng": Decimal("-98.3959"),
            },
            {
                "name": "Oscorp Labs",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1965-07-22",
                "containment_level": 4,
                "dimensional_stability": Decimal("76.5"),
                "is_evil": True,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "PSI Tech Labs",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1985-07-15",
                "containment_level": 3,
                "dimensional_stability": Decimal("68.3"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Pym Laboratories",
                "universe": universes["Marvel"],
                "location": "San Francisco, CA",
                "established_date": "1975-08-18",
                "containment_level": 3,
                "dimensional_stability": Decimal("95.0"),
                "is_evil": False,
                "location_lat": Decimal("37.7749"),  # San Francisco, CA coordinates
                "location_lng": Decimal("-122.4194"),
            },
            {
                "name": "Reed's Laboratory",
                "universe": universes["Marvel"],
                "location": "Baxter Building, Manhattan",
                "established_date": "1961-11-08",
                "containment_level": 4,
                "dimensional_stability": Decimal("94.7"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Baxter Building, Manhattan coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "Ryking Hospital for Parahuman Research",
                "universe": universes["Marvel"],
                "location": "New Mexico",
                "established_date": "1968-12-25",
                "containment_level": 4,
                "dimensional_stability": Decimal("79.9"),
                "is_evil": True,
                "location_lat": Decimal("34.4048"),  # New Mexico coordinates
                "location_lng": Decimal("-106.9056"),
            },
            {
                "name": "Rockfort Island Facility",
                "universe": universes["Resident Evil"],
                "location": "Rockfort Island",
                "established_date": "1990-07-22",
                "containment_level": 4,
                "dimensional_stability": Decimal("65.4"),
                "is_evil": True,
                "location_lat": Decimal("35.0000"),  # Rockfort Island (fictional, based on Japan)
                "location_lng": Decimal("138.0000"),
            },
            {
                "name": "S.T.A.R. Labs - Central City",
                "universe": universes["DC"],
                "location": "Central City",
                "established_date": "1970-03-08",
                "containment_level": 4,
                "dimensional_stability": Decimal("37.4"),
                "is_evil": False,
                "location_lat": Decimal("39.7684"),  # Central City (fictional, based on Midwest USA)
                "location_lng": Decimal("-86.1581"),
            },
            {
                "name": "S.T.A.R. Labs - Gotham City",
                "universe": universes["DC"],
                "location": "Gotham City",
                "established_date": "1970-05-22",
                "containment_level": 4,
                "dimensional_stability": Decimal("72.1"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Gotham City (fictional, based on New York City)
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "S.T.A.R. Labs - Metropolis",
                "universe": universes["DC"],
                "location": "Metropolis",
                "established_date": "1970-04-15",
                "containment_level": 4,
                "dimensional_stability": Decimal("89.2"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Metropolis (fictional, based on New York City)
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "SCP Containment Facility",
                "universe": universes["SCP"],
                "location": "[REDACTED]",
                "established_date": "1956-06-06",
                "containment_level": 5,
                "dimensional_stability": Decimal("55.5"),
                "is_evil": False,
                "location_lat": Decimal("0.0000"),  # Unknown location (placeholder)
                "location_lng": Decimal("0.0000"),
            },
            {
                "name": "Site-17",
                "universe": universes["SCP"],
                "location": "[REDACTED]",
                "established_date": "1970-05-15",
                "containment_level": 5,
                "dimensional_stability": Decimal("88.9"),
                "is_evil": False,
                "location_lat": Decimal("0.0000"),  # Unknown location (placeholder)
                "location_lng": Decimal("0.0000"),
            },
            {
                "name": "Site-81",
                "universe": universes["SCP"],
                "location": "[REDACTED]",
                "established_date": "1975-09-30",
                "containment_level": 4,
                "dimensional_stability": Decimal("12.3"),
                "is_evil": False,
                "location_lat": Decimal("0.0000"),  # Unknown location (placeholder)
                "location_lng": Decimal("0.0000"),
            },
            {
                "name": "Spencer Mansion Facility",
                "universe": universes["Resident Evil"],
                "location": "Arklay Mountains",
                "established_date": "1962-05-15",
                "containment_level": 5,
                "dimensional_stability": Decimal("45.5"),
                "is_evil": True,
                "location_lat": Decimal("35.0000"),  # Arklay Mountains (fictional, based on Japan)
                "location_lng": Decimal("138.0000"),
            },
            {
                "name": "Stark Industries Lab",
                "universe": universes["Marvel"],
                "location": "Manhattan, NY",
                "established_date": "1940-03-15",
                "containment_level": 4,
                "dimensional_stability": Decimal("38.9"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Manhattan, NY coordinates
                "location_lng": Decimal("-74.0060"),
            },
            {
                "name": "The Flame Station",
                "universe": universes["Lost"],
                "location": "The Island",
                "established_date": "1976-08-20",
                "containment_level": 3,
                "dimensional_stability": Decimal("79.5"),
                "is_evil": False,
                "location_lat": Decimal("-12.0000"),  # The Island (fictional, based on Pacific Ocean)
                "location_lng": Decimal("-157.0000"),
            },
            {
                "name": "The Hydra Station",
                "universe": universes["Lost"],
                "location": "The Island",
                "established_date": "1975-06-15",
                "containment_level": 3,
                "dimensional_stability": Decimal("47.8"),
                "is_evil": False,
                "location_lat": Decimal("-12.0000"),  # The Island (fictional, based on Pacific Ocean)
                "location_lng": Decimal("-157.0000"),
            },
            {
                "name": "The Orchid",
                "universe": universes["Lost"],
                "location": "The Island",
                "established_date": "1977-08-15",
                "containment_level": 3,
                "dimensional_stability": Decimal("65.2"),
                "is_evil": False,
                "location_lat": Decimal("-12.0000"),  # The Island (fictional, based on Pacific Ocean)
                "location_lng": Decimal("-157.0000"),
            },
            {
                "name": "The Swan Laboratory",
                "universe": universes["Lost"],
                "location": "The Island",
                "established_date": "1977-07-07",
                "containment_level": 3,
                "dimensional_stability": Decimal("42.7"),
                "is_evil": False,
                "location_lat": Decimal("-12.0000"),  # The Island (fictional, based on Pacific Ocean)
                "location_lng": Decimal("-157.0000"),
            },
            {
                "name": "Umbrella Corporation Paris Laboratory",
                "universe": universes["Resident Evil"],
                "location": "Paris, France",
                "established_date": "1988-04-15",
                "containment_level": 5,
                "dimensional_stability": Decimal("60.8"),
                "is_evil": True,
                "location_lat": Decimal("48.8566"),  # Paris, France coordinates
                "location_lng": Decimal("2.3522"),
            },
            {
                "name": "WayneTech Research & Development",
                "universe": universes["DC"],
                "location": "Gotham City",
                "established_date": "1980-06-12",
                "containment_level": 3,
                "dimensional_stability": Decimal("92.5"),
                "is_evil": False,
                "location_lat": Decimal("40.7128"),  # Gotham City (fictional, based on New York City)
                "location_lng": Decimal("-74.0060"),
            },
        ]

        # Create laboratories
        created_labs = []
        for lab_data in laboratories:
            lab = self.create_laboratory(**lab_data)
            created_labs.append(lab)
            self.stdout.write(f"Created laboratory: {lab.name}")

            # Create related data for each laboratory
            self.create_experimental_devices(lab)
            self.create_anomalous_substances(lab)
            self.create_test_subjects(lab)
            self.create_incident_reports(lab)
            self.create_dimensional_rifts(lab)
            self.create_safety_protocols(lab)
            self.create_energy_readings(lab)

        self.stdout.write(self.style.SUCCESS("Successfully populated database"))

    def create_universe(self, name, description, year):
        """Create a fictional universe with the given data."""
        return Universe.objects.create(
            name=name,
            description=description,
            year_introduced=year,
        )

    def create_laboratory(self, **kwargs):
        """Create a laboratory with the given data."""
        return Laboratory.objects.create(**kwargs)

    def create_experimental_devices(self, lab):
        """Create fictional experimental devices for the laboratory."""
        device_names = [
            "Quantum Accelerator",
            "Temporal Displacement Engine",
            "Reality Warper",
            "Matter Reconstructor",
            "Neural Interface",
            "Flux Capacitor",
            "Interdimensional Portal Generator",
            "Particle Collider",
            "Tachyon Enhancement Chamber",
            "Molecular Disassembler",
            "Gravitational Wave Detector",
            "Dark Matter Containment Unit",
            "Anti-Matter Synthesizer",
            "Quantum Entanglement Scanner",
            "Time Dilation Field Generator",
            "Neural Pattern Rewriter",
            "Consciousness Transfer Device",
            "Reality Matrix Stabilizer",
            "Probability Manipulator",
            "Dimensional Breach Detector",
            "Excision Beam Emitter",
            "Ambient Morality Field",
            "Pronged Quantum Slicer",
            "Liquid Reality Injector",
            "Query Engine",
            "Hostile Environment Suit",
            "Mutagenic Ray Emitter",
            "Slipstream Drive",
            "Sonic Screwdriver",
            "Infinite Improbability Drive",
            "Hyperspace Engine",
            "Tardis",
            "Neuralyzer",
            "Kronos Device",
            "Partial Immortality Serum",
            "Chronal Displacement Array",
            "Ambrosia Generator",
        ]

        # Create 5-8 random devices for each lab
        selected_devices = random.sample(device_names, random.randint(5, 8))
        for name in selected_devices:
            # Create device with appropriate ranges based on device type
            if "Quantum" in name or "Particle" in name:
                # High power, high precision devices
                ExperimentalDevice.objects.create(
                    name=name,
                    laboratory=lab,
                    fuel_tank_capacity=random.randint(500, 2000),
                    memory_capacity=random.randint(512, 2048),
                    power_output=Decimal(str(random.uniform(5.0000, 20.0000))),
                    quantum_uncertainty=Decimal(str(random.uniform(0.00001, 0.001))),
                    dimensional_wavelength=Decimal(str(random.uniform(0.100, 1.000))),
                    portal_diameter=Decimal(str(random.uniform(0.100, 1.000))),
                )
            elif "Time" in name or "Temporal" in name:
                # Time-based devices with unique characteristics
                ExperimentalDevice.objects.create(
                    name=name,
                    laboratory=lab,
                    fuel_tank_capacity=random.randint(1000, 5000),
                    memory_capacity=random.randint(2048, 4096),
                    power_output=Decimal(str(random.uniform(15.0000, 50.0000))),
                    quantum_uncertainty=Decimal(str(random.uniform(0.01, 0.1))),
                    dimensional_wavelength=Decimal(str(random.uniform(50, 200))),
                    portal_diameter=Decimal(str(random.uniform(2.00, 10.00))),
                )
            else:
                # Standard experimental devices
                ExperimentalDevice.objects.create(
                    name=name,
                    laboratory=lab,
                    fuel_tank_capacity=random.randint(100, 1000),
                    memory_capacity=random.randint(128, 16384),
                    power_output=Decimal(str(random.uniform(0.1, 100.0))),
                    quantum_uncertainty=Decimal(str(random.uniform(0.0001, 0.1))),
                    dimensional_wavelength=Decimal(str(random.uniform(1, 100))),
                    portal_diameter=Decimal(str(random.uniform(0.5, 50.0))),
                )

    def create_anomalous_substances(self, lab):
        """Create fictional anomalous substances for the laboratory."""
        substance_names = [
            "Quantum Fluid",
            "Time Crystal",
            "Dark Matter Sample",
            "Antimatter Residue",
            "Dimensional Plasma",
            "Tachyonic Condensate",
            "Exotic Matter",
            "Strange Matter",
            "Quark-Gluon Plasma",
            "Meta-Stable Element",
            "Living Metal",
            "Probability Fluid",
            "Memory Crystal",
            "Bio-Digital Matrix",
            "Quantum Entangled Particles",
            "Temporal Distortion Gel",
            "Reality Anchor Material",
            "Consciousness Crystal",
            "High-Sodium Incel Tears",
            "Void Matter",
            "Dimensional Shards",
            "Hyper-Condensed Energy",
            "Oblique Matter",
            "Mushroom Cloud Residue",
            "Warped Space-Time Fragment",
            "Graviton Resonance Dust",
            "Quantum Foam",
            "Inexplicable Mudpie",
            "Chaos Crystal",
            "Schrödinger's Cat Hairball",
            "Reality Dust",
            "T-Vaccine",
            "Nanite Swarm",
            "Horrorfrost",
            "Hollow Reality Shard",
            "Ambrosia",
            "Transmogrification Serum",
            "Ectoplasmic Residue",
        ]

        # Create 4-7 random substances for each lab
        selected_substances = random.sample(substance_names, random.randint(4, 7))
        for name in selected_substances:
            # Adjust properties based on substance type
            if "Quantum" in name or "Quark" in name:
                # Ultra-cold substances
                AnomalousSubstance.objects.create(
                    name=name,
                    laboratory=lab,
                    containment_temperature=Decimal(str(random.uniform(0.001, 1.000))),
                    container_volume=random.randint(10, 100),
                    critical_mass=Decimal(str(random.uniform(0.00001, 0.001))),
                    half_life=Decimal(str(random.uniform(0.01, 10.0))),
                    typical_shelf_life=random.randint(1, 7),
                    reality_warping_field=Decimal(str(random.uniform(0.01, 0.5))),
                )
            elif "Plasma" in name or "Matter" in name:
                # High-energy substances
                AnomalousSubstance.objects.create(
                    name=name,
                    laboratory=lab,
                    containment_temperature=Decimal(str(random.uniform(1000, 5000))),
                    container_volume=random.randint(500, 20000),
                    critical_mass=Decimal(str(random.uniform(0.10, 100.0))),
                    half_life=Decimal(str(random.uniform(100, 10000))),
                    typical_shelf_life=random.randint(365, 3650),
                    reality_warping_field=Decimal(str(random.uniform(0.8, 1.0))),
                )
            else:
                # Standard anomalous substances
                AnomalousSubstance.objects.create(
                    name=name,
                    laboratory=lab,
                    containment_temperature=Decimal(str(random.uniform(0.1, 373.15))),
                    container_volume=random.randint(10, 1000),
                    critical_mass=Decimal(str(random.uniform(0.001, 10.0))),
                    half_life=Decimal(str(random.uniform(1, 365))),
                    typical_shelf_life=random.randint(30, 365),
                    reality_warping_field=Decimal(str(random.uniform(0.0001, 1.0))),
                )

    def create_test_subjects(self, lab):
        """Create fictional test subjects for the laboratory."""
        for i in range(random.randint(3, 7)):
            TestSubject.objects.create(
                identifier=f"TS-{lab.pk}-{i:03d}",
                laboratory=lab,
                creation_date=timezone.now() - timedelta(days=random.randint(1, 365)),
                intelligence_quotient=random.randint(80, 230),
                processing_speed=Decimal(str(random.uniform(100, 2500))),
                power_consumption=Decimal(str(random.uniform(10, 2300))),
            )

    def create_incident_reports(self, lab):
        """Create fictional incident reports for the laboratory."""
        incident_descriptions = [
            "Containment breach",
            "Reality destabilization",
            "Temporal anomaly",
            "Dimensional rift formation",
            "Test subject escape attempt",
            "Energy overload",
            "Anomalous substance spill",
            "Personnel transmutation",
            "Equipment zero-point failure",
            "Quantum entanglement cascade",
            "Reality anchor failure",
            "Unintended headquarters relocation",
            "Y2K incident",
            "Wave-particle duality collapse",
            "Hot tub time machine incident",
            "Dark energy feedback loop",
            "Tachyon resonance cascade",
            "Recursive time loop loop loop",
            "Probability inversion event",
            "Consciousness transfer malfunction",
            "Unperturbed perturbation",
            "Meta-resistant meta-material",
            "Abbreivated lifespan syndrome",
            "Implausible deniability",
            "Aftershock due to xerothermic activity",
            "Chronological displacement",
            "Long-range vibration destabilization",
            "Instant dark matter expansion",
            "AI duality event",
            "Crumbled space-time continuum",
            "Quantum foam overflow",
            "Johnny brought cookies into the lab again",
            "Ultranormal activity",
            "Binary becoming ternary",
            "Quantum superposition collapse",
            "Jellyfish nebula formation",
            "Mundane reality incursion",
            "Zero-point energy fluctuation",
            "Quality assurance oversight",
            "Weather control malfunction",
            "Unintended reality shift",
            "Interior volume greater than exterior",
            "Sharknado",
            "Spacefaring sea slug infestation",
            "Mechanical sheep disaster",
            "Localized de-simulation",
            "Inclement galactic convergence",
        ]

        for description in incident_descriptions:
            if random.random() < 0.21:  # 21% chance of each incident occurring
                IncidentReport.objects.create(
                    laboratory=lab,
                    timestamp=timezone.now() - timedelta(days=random.randint(1, 365)),
                    description=description,
                    severity=random.randint(1, 5),
                    affected_radius=Decimal(str(random.uniform(0.1, 100))),
                    temporal_displacement=Decimal(str(random.uniform(0, 100))),
                )

    def create_dimensional_rifts(self, lab):
        """Create fictional dimensional rifts for the laboratory."""
        for _ in range(random.randint(1, 3)):
            DimensionalRift.objects.create(
                laboratory=lab,
                detected_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                is_stable=random.choice([True, False]),
                diameter=Decimal(str(random.uniform(0.1, 100.0))),
                energy_output=Decimal(str(random.uniform(100, 10000))),
                spacetime_curvature=Decimal(str(random.uniform(0.001, 0.1))),
            )

    def create_safety_protocols(self, lab):
        """Create fictional safety protocols for the laboratory."""
        protocol_names = [
            "Emergency Containment",
            "Reality Anchor",
            "Temporal Stabilization",
            "Dimensional Seal",
            "Subject Control",
            "Quantum Stabilization",
            "Anti-Matter Containment",
            "Dark Energy Suppression",
            "Void Collapse Prevention",
            "Timeline Protection",
            "Consciousness Firewall",
            "Bio-Digital Quarantine",
            "Reality Matrix Maintenance",
            "Dimensional Breach Control",
            "Paradox Prevention",
            "Memory Protection",
            "Probability Field Control",
            "Exotic Matter Containment",
            "Neural Pattern Security",
            "Space-Time Integrity",
            "Quantum Entanglement Lock",
            "Tachyon Shielding",
            "Matter Reconstitution",
            "Gravitational Wave Dampening",
            "Johnny's cookie containment",
            "Jellyfish nebula stabilization",
            "Mundane reality reinforcement",
            "Zero-point energy suppression",
            "Quality assurance lockdown",
            "Weather control override",
            "Kitten containment",
            "Unintended reality shift reversal",
            "Interior volume correction",
            "Sharknado direction reversal",
            "Reality Matrix Reboot",
            "Y2K19 incident prevention",
            "AI duality to unity conversion",
            "Ternary operator conversion",
        ]

        # Create 6-10 protocols for each lab based on containment level
        num_protocols = 6 + lab.containment_level  # More dangerous labs get more protocols
        selected_protocols = random.sample(protocol_names, num_protocols)

        for name in selected_protocols:
            # Adjust protocol parameters based on type and lab's containment level
            base_field_strength = 100 * lab.containment_level
            base_frequency = 200 * lab.containment_level

            if "Containment" in name or "Protection" in name:
                # Defensive protocols - higher field strength
                SafetyProtocol.objects.create(
                    laboratory=lab,
                    name=name,
                    description=f"Primary containment protocol for {name.lower()} scenarios",
                    containment_field_strength=Decimal(
                        str(random.uniform(base_field_strength * 1.5, base_field_strength * 2.0))
                    ),
                    shield_frequency=Decimal(str(random.uniform(base_frequency * 0.8, base_frequency * 10.2))),
                )
            elif "Reality" in name or "Dimensional" in name:
                # Reality-affecting protocols - higher frequencies
                SafetyProtocol.objects.create(
                    laboratory=lab,
                    name=name,
                    description=f"Advanced protocol for maintaining {name.lower()}",
                    containment_field_strength=Decimal(
                        str(random.uniform(base_field_strength * 0.8, base_field_strength * 10.2))
                    ),
                    shield_frequency=Decimal(str(random.uniform(base_frequency * 1.15, base_frequency * 20.0))),
                )
            else:
                # Standard protocols
                SafetyProtocol.objects.create(
                    laboratory=lab,
                    name=name,
                    description=f"Standard protocol for {name.lower()} procedures",
                    containment_field_strength=Decimal(
                        str(random.uniform(base_field_strength * 0.2, base_field_strength * 0.6))
                    ),
                    shield_frequency=Decimal(str(random.uniform(base_frequency * 0.9, base_frequency * 1.1))),
                )

    def create_energy_readings(self, lab):
        """Create fictional energy readings for the laboratory."""
        # Readings for the past week
        for days_ago in range(7):
            timestamp = timezone.now() - timedelta(days=days_ago)
            for _ in range(random.randint(3, 8)):  # Multiple readings per day
                EnergyReading.objects.create(
                    laboratory=lab,
                    timestamp=timestamp - timedelta(hours=random.randint(0, 23)),
                    background_radiation=Decimal(str(random.uniform(10.000, 500000.000))),
                    tachyon_flux=Decimal(str(random.uniform(1000, 1250000))),
                    dark_energy_density=Decimal(str(random.uniform(10.0, 2200000000.0))),
                )
