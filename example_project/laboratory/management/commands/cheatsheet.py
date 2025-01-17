"""Django Pint Field demonstration management command.

Run with: python manage.py demo_pint_fields
"""

from django.core.management.base import BaseCommand
from tabulate import tabulate

from django_pint_field.aggregates import PintAvg
from django_pint_field.aggregates import PintMax
from django_pint_field.aggregates import PintStdDev
from example_project.laboratory.models import ExperimentalDevice


class Command(BaseCommand):
    """Demonstration of Django Pint Field features."""

    help = "Display comprehensive examples of manipulating field value outputs in the console and code."

    def create_demo_row(self, description, code, device=None, devices=None):
        """Create a row for the demo table by executing code and capturing output."""
        try:
            # If device is provided, make it available to the code being executed
            if device:
                locals()["device"] = device
            if devices:
                locals()["devices"] = devices
            result = eval(code)
            return [description, code, str(result)]
        except Exception as e:
            return [description, code, f"Error: {str(e)}"]

    def print_section(self, title, rows):
        """Print a section of the demo with tabulated output."""
        self.stdout.write(self.style.SUCCESS(f"\n=== {title} ==="))
        headers = ["Description", "Code", "Output"]
        self.stdout.write(tabulate(rows, headers=headers, tablefmt="grid"))

    def demo_basic_field_access(self, device):
        """Demonstrate basic field access and properties."""
        rows = [
            # Basic field access
            self.create_demo_row("Field type", "type(device.portal_diameter)", device),
            self.create_demo_row("Direct string output", "device.portal_diameter", device),
            self.create_demo_row("Magnitude", "device.portal_diameter.magnitude", device),
            self.create_demo_row("Units", "device.portal_diameter.units", device),
            # Quantity access
            self.create_demo_row("Quantity type", "type(device.portal_diameter.quantity)", device),
            self.create_demo_row("Quantity value", "device.portal_diameter.quantity", device),
            self.create_demo_row("Quantity magnitude", "device.portal_diameter.quantity.magnitude", device),
            self.create_demo_row("Quantity units", "device.portal_diameter.quantity.units", device),
            # get_FOO_display() method
            self.create_demo_row("get_FOO_display() method", "device.get_portal_diameter_display()", device),
            self.create_demo_row(
                "get_FOO_display() with digits", "device.get_portal_diameter_display(digits=3)", device
            ),
            self.create_demo_row(
                "get_FOO_display() with format_string", "device.get_portal_diameter_display(format_string='~P')", device
            ),
            self.create_demo_row(
                "get_FOO_display() with digits and format_string",
                "device.get_portal_diameter_display(digits=3, format_string='~P')",
                device,
            ),
        ]
        self.print_section("Basic Field Access", rows)

    def demo_unit_conversions(self, device):
        """Demonstrate unit conversion methods."""
        rows = [
            # Proxy attribute conversions
            self.create_demo_row(
                "Convert to kilometers (proxy)",
                "device.portal_diameter.kilometer",
                device,
            ),
            self.create_demo_row(
                "Convert to centimeters (proxy)",
                "device.portal_diameter.centimeter",
                device,
            ),
            self.create_demo_row(
                "Convert to millimeters (proxy)",
                "device.portal_diameter.millimeter",
                device,
            ),
            # Quantity.to() conversions
            self.create_demo_row(
                "Convert to kilometers (quantity)",
                "device.portal_diameter.quantity.to('kilometer')",
                device,
            ),
            self.create_demo_row(
                "Convert to centimeters (quantity)",
                "device.portal_diameter.quantity.to('centimeter')",
                device,
            ),
            self.create_demo_row(
                "Convert to millimeters (quantity)",
                "device.portal_diameter.quantity.to('millimeter')",
                device,
            ),
        ]
        self.print_section("Unit Conversions", rows)

    def demo_decimal_formatting(self, device):
        """Demonstrate decimal place formatting."""
        rows = [
            # Using digits__ syntax
            self.create_demo_row("Format with 2 decimal places", "device.portal_diameter.digits__2", device),
            self.create_demo_row("Format with 3 decimal places", "device.portal_diameter.digits__3", device),
            self.create_demo_row("Format with 4 decimal places", "device.portal_diameter.digits__4", device),
            # Unit conversion with decimal places
            self.create_demo_row("Convert to km with 3 decimal places", "device.portal_diameter.kilometer__3", device),
            self.create_demo_row("Convert to cm with 2 decimal places", "device.portal_diameter.centimeter__2", device),
            self.create_demo_row("Convert to mm with 1 decimal place", "device.portal_diameter.millimeter__1", device),
        ]
        self.print_section("Decimal Formatting", rows)

    def demo_aggregations(self):
        """Demonstrate aggregation functions."""
        # Calculate aggregates
        aggs = ExperimentalDevice.objects.aggregate(
            avg_diameter=PintAvg("portal_diameter"),
            max_diameter=PintMax("portal_diameter"),
            std_dev_diameter=PintStdDev("portal_diameter"),
        )
        agg_classes = [
            PintAvg.__name__,
            PintMax.__name__,
            PintStdDev.__name__,
        ]

        rows = []
        rows.extend(
            [
                self.create_demo_row(
                    "count",
                    "ExperimentalDevice.objects.aggregate(count=PintCount('portal_diameter'))['count']",
                ),
            ]
        )
        for i, (key, value) in enumerate(aggs.items()):
            rows.extend(
                [
                    self.create_demo_row(
                        f"{key} base value",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}']",
                    ),
                    self.create_demo_row(
                        f"{key} raw Quantity",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}'].quantity",
                    ),
                    self.create_demo_row(
                        f"{key} raw Quantity magnitude",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}'].quantity.magnitude",
                    ),
                    self.create_demo_row(
                        f"{key} raw Quantity converted to km",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}'].quantity.to('kilometer')",
                    ),
                    self.create_demo_row(
                        f"{key} in centimeters",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}'].centimeter",
                    ),
                    self.create_demo_row(
                        f"{key} formatted (2 places)",
                        f"ExperimentalDevice.objects.aggregate({key}={agg_classes[i]}('portal_diameter'))['{key}'].digits__2",
                    ),
                ]
            )
        self.print_section("Aggregations", rows)

    def demo_advanced_features(self, device):
        """Demonstrate advanced features and combinations."""
        rows = [
            # Combining conversions with formatting
            self.create_demo_row(
                "Original value",
                "device.portal_diameter",
                device,
            ),
            self.create_demo_row(
                "To km with 3 decimal places",
                "device.portal_diameter.kilometer__3",
                device,
            ),
            self.create_demo_row(
                "To cm with 2 decimal places",
                "device.portal_diameter.centimeter__2",
                device,
            ),
            # Components after conversion
            self.create_demo_row(
                "Kilometer conversion magnitude",
                "device.portal_diameter.kilometer.magnitude",
                device,
            ),
            self.create_demo_row(
                "Kilometer conversion units",
                "device.portal_diameter.kilometer.units",
                device,
            ),
        ]
        self.print_section("Advanced Features", rows)

    def demo_comparison_operations(self):
        """Demonstrate comparison operations."""
        devices = ExperimentalDevice.objects.all()[:2]
        if len(devices) >= 2:
            d1, d2 = devices
            rows = [
                self.create_demo_row(
                    "First device diameter",
                    "devices[0].portal_diameter",
                    devices=devices,
                ),
                self.create_demo_row(
                    "Second device diameter",
                    "devices[1].portal_diameter",
                    devices=devices,
                ),
                self.create_demo_row(
                    "Equal comparison",
                    "devices[0].portal_diameter.quantity == devices[1].portal_diameter.quantity",
                    devices=devices,
                ),
                self.create_demo_row(
                    "Greater than comparison",
                    "devices[0].portal_diameter.quantity > devices[1].portal_diameter.quantity",
                    devices=devices,
                ),
                self.create_demo_row(
                    "Less than comparison",
                    "devices[0].portal_diameter.quantity < devices[1].portal_diameter.quantity",
                    devices=devices,
                ),
            ]
            self.print_section("Comparison Operations", rows)

    def demo_field_metadata(self):
        """Demonstrate access to field metadata."""
        field = ExperimentalDevice._meta.get_field("portal_diameter")
        rows = [
            self.create_demo_row(
                "Default unit",
                "ExperimentalDevice._meta.get_field('portal_diameter').default_unit",
            ),
            self.create_demo_row(
                "Unit choices",
                "ExperimentalDevice._meta.get_field('portal_diameter').unit_choices",
            ),
            self.create_demo_row(
                "Display decimal places",
                "getattr(ExperimentalDevice._meta.get_field('portal_diameter'), 'display_decimal_places', None)",
            ),
        ]
        self.print_section("Field Metadata", rows)

    def handle(self, *args, **options):
        """Run all demonstrations."""
        self.stdout.write(self.style.SUCCESS("Running Django Pint Field demonstrations..."))

        # Get a sample device
        device = ExperimentalDevice.objects.first()
        if not device:
            self.stdout.write(self.style.ERROR("No experimental devices found in database."))
            return

        # Run all demos
        self.demo_basic_field_access(device)
        self.demo_unit_conversions(device)
        self.demo_decimal_formatting(device)
        self.demo_aggregations()
        self.demo_advanced_features(device)
        self.demo_comparison_operations()
        self.demo_field_metadata()
