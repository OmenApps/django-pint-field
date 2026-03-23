# Configuring and Working with PintFields

## Choosing Between IntegerPintField and DecimalPintField

`IntegerPintField` stores quantities as whole numbers. Use it for counts, simple measurements, or anything where fractional values are irrelevant.

`DecimalPintField` stores quantities with full decimal precision. Use it for scientific measurements, financial calculations, or any situation where you need fractional values. It supports `display_decimal_places` and `rounding_method` parameters for fine-grained control over how values are displayed and rounded.

Both field types store the comparator (used for cross-unit database comparisons) as a `Decimal` internally, so comparisons remain accurate regardless of which field type you choose.

## Configuring unit_choices

The `unit_choices` parameter controls which units appear in forms and widgets. You can specify it in several formats:

```python
# Simple string list
unit_choices=["gram", "kilogram", "pound"]

# With display names
unit_choices=[
    ("Gram", "gram"),
    ("Kilogram", "kilogram"),
    ("Pound", "pound"),
]

# Mixed format
unit_choices=[
    "gram",
    ("Kilogram", "kilogram"),
    ["Pound", "pound"],
]
```

The `default_unit` is always added internally even if you do not include it in `unit_choices`. All units listed in `unit_choices` must share the same dimensionality as the `default_unit`.

## Defining and Using Custom Units

Pint lets you define arbitrary units through its `UnitRegistry`. This is useful for domain-specific quantities like servings, scoops, or any measurement not covered by standard SI or imperial units.

### Creating Custom Unit Definitions

Create a new registry and define your units. This belongs in a dedicated configuration file or in your Django settings module.

```python
from decimal import Decimal
from pint import UnitRegistry

# Create a new registry with Decimal support
custom_ureg = UnitRegistry(non_int_type=Decimal)

# Define basic custom units
custom_ureg.define("serving = [serving]")  # Base unit for serving sizes
custom_ureg.define("scoop = 2 * serving")  # Define a scoop as 2 servings
custom_ureg.define("portion = 4 * serving")  # Define a portion as 4 servings

# Define derived units
custom_ureg.define("calorie_density = calorie / gram")  # Energy density
custom_ureg.define("price_per_kg = dollar / kilogram")  # Price density

# Define prefixed units
custom_ureg.define("halfserving = 0.5 * serving")
custom_ureg.define("doubleserving = 2 * serving")
```

For the full syntax and capabilities, see the [Pint documentation on defining units](https://pint.readthedocs.io/en/stable/advanced/defining.html).

### Registering Custom Units

Tell Django Pint Field to use your custom registry by setting it in `settings.py`:

```python
# settings.py

# Set the custom registry as the default for the project
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
```

### Using Custom Units in Models

Once registered, custom units work the same as built-in ones:

```python
from django.db import models
from django_pint_field.models import DecimalPintField


class Recipe(models.Model):
    name = models.CharField(max_length=100)
    serving_size = DecimalPintField(
        "serving",  # Using our custom base unit
        display_decimal_places=2,
        unit_choices=[
            "serving",
            "scoop",
            "portion",
            "halfserving",
        ],
    )
    energy_density = DecimalPintField(
        "calorie_density",  # Using our custom derived unit
        display_decimal_places=2,
    )

    def __str__(self):
        return self.name
```

## Controlling Decimal Precision and Rounding

### Precision Management

Control decimal precision at the global level and per field:

```python
# Global precision setting in settings.py
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 28  # Set project-wide precision


# Model-level precision control
class PreciseWeight(models.Model):
    # Field with specific precision requirements
    weight = DecimalPintField(
        "gram",
        display_decimal_places=4,  # Decimal places to display by default
        unit_choices=["gram", "kilogram", "pound"],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(weight__isnull=False),
                name="weight_not_null",
            )
        ]
```

### Rounding Strategies

The `rounding_method` parameter on `DecimalPintField` accepts any of the standard `decimal` module rounding modes:

- `ROUND_HALF_UP` (default)
- `ROUND_DOWN`
- `ROUND_CEILING`
- `ROUND_FLOOR`
- `ROUND_HALF_DOWN`
- `ROUND_HALF_EVEN`
- `ROUND_UP`
- `ROUND_05UP`

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_CEILING
from django_pint_field.units import ureg


class WeightMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
        rounding_method=ROUND_HALF_UP,  # Default rounding method
    )

    def round_weight(self, method=ROUND_HALF_UP, places=2):
        """Round weight using specified method and decimal places"""
        if self.weight:
            magnitude = Decimal(str(self.weight.magnitude))
            rounded = magnitude.quantize(Decimal("0.01"), rounding=method)
            return ureg.Quantity(rounded, self.weight.units)
        return None

    def get_rounded_weights(self):
        """Get weight rounded using different methods"""
        return {
            "half_up": self.round_weight(ROUND_HALF_UP),
            "down": self.round_weight(ROUND_DOWN),
            "ceiling": self.round_weight(ROUND_CEILING),
        }
```

### Decimal Context Configuration

For calculations that need temporary higher precision, use Python's `localcontext`:

```python
from decimal import getcontext, localcontext
from django_pint_field.units import ureg


class HighPrecisionMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        display_decimal_places=10,
    )

    def precise_calculation(self):
        """Perform high-precision calculations"""
        with localcontext() as ctx:
            # Temporarily set higher precision for this calculation
            ctx.prec = 50

            if self.value:
                # Perform precise calculation
                result = (self.value**2).magnitude
                # Return with original precision
                return Decimal(str(result)).quantize(Decimal("0.0000000001"))

    @staticmethod
    def set_global_precision(precision):
        """Set global decimal precision"""
        getcontext().prec = precision
```

## Working with Derived Units

Derived units combine multiple base units. They are useful for quantities like velocity, acceleration, density, and similar computed measurements.

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class PhysicalMeasurement(models.Model):
    # Basic measurements
    length = DecimalPintField(
        "meter",
        display_decimal_places=2,
    )
    time = DecimalPintField(
        "second",
        display_decimal_places=2,
    )

    # Derived measurements
    velocity = DecimalPintField(
        "meter/second",
        display_decimal_places=2,
    )
    acceleration = DecimalPintField(
        "meter/second**2",
        display_decimal_places=2,
    )

    def calculate_velocity(self):
        """Calculate velocity from length and time"""
        if self.length and self.time:
            try:
                self.velocity = self.length / self.time
                return self.velocity
            except Exception as e:
                raise ValueError(f"Velocity calculation error: {e}")

    def calculate_acceleration(self):
        """Calculate acceleration from velocity and time"""
        if self.velocity and self.time:
            try:
                self.acceleration = self.velocity / self.time
                return self.acceleration
            except Exception as e:
                raise ValueError(f"Acceleration calculation error: {e}")
```

## Validating PintField Values

### Built-in Validation

PintFields automatically validate dimensionality. If you define a field with `default_unit="gram"`, assigning a length quantity (like meters) raises a `ValidationError`. When using `DecimalPintField`, decimal validation follows the active Decimal context precision; `display_decimal_places` controls rendering, not storage precision.

### Custom Validation in clean()

Add range checks and other constraints in your model's `clean()` method:

```python
from django.core.exceptions import ValidationError
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class ValidatedMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        display_decimal_places=2,
        unit_choices=["meter", "kilometer", "mile"],
    )

    def clean(self) -> None:
        """Validate measurement"""
        if self.value is not None:
            # Validate range
            if self.value.quantity.to("meter").magnitude > 1000000:
                raise ValidationError("Value cannot exceed 1,000,000 meters")

    def save(self, *args, **kwargs) -> None:
        """Save with validation"""
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_valid_units(cls) -> list:
        """Get list of valid units"""
        field = cls._meta.get_field("value")
        return field.unit_choices
```

### Range Validation with Decimal Precision

For tighter control, use `Decimal` values in your range checks:

```python
from decimal import Decimal
from django_pint_field.units import ureg


class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
        unit_choices=["gram", "kilogram"],
    )

    def clean(self):
        super().clean()
        if self.weight:
            # Dimensionality validation is automatic;
            # assigning a length unit to a weight field raises ValidationError

            # Custom range validation with Decimal precision
            min_weight = Decimal("0.1") * ureg.kilogram
            max_weight = Decimal("100.0") * ureg.kilogram

            if self.weight < min_weight:
                raise ValidationError(
                    {"weight": f"Weight must be at least {min_weight:.2f}"}
                )
            if self.weight > max_weight:
                raise ValidationError(
                    {"weight": f"Weight cannot exceed {max_weight:.2f}"}
                )

            # Decimal precision validation follows the active Decimal context;
            # display_decimal_places only affects rendering
```

## Building Reusable Conversion Utilities

A mixin keeps conversion logic in one place and avoids repeating the same patterns across models:

```python
from typing import Dict, Any, Optional
from decimal import Decimal
from django_pint_field.units import ureg


class ConversionMixin:
    """Mixin for common conversion patterns"""

    def to_unit(self, unit: str, round_digits: int = 2) -> ureg.Quantity:
        """Convert to specified unit with rounding"""
        if self.value is None:
            return None

        converted = self.value.quantity.to(unit)
        magnitude = Decimal(str(converted.magnitude))
        rounded = round(magnitude, round_digits)
        return ureg.Quantity(rounded, unit)

    def get_all_units(self) -> Dict[str, Any]:
        """Get value in all available units"""
        if self.value is None:
            return {}

        return {unit_value: self.to_unit(unit_value) for _label, unit_value in self.get_valid_units()}

    def format_value(self, unit: Optional[str] = None, decimal_places: int = 2) -> str:
        """Format value for display"""
        if self.value is None:
            return ""

        value = self.to_unit(unit) if unit else self.value.quantity
        return f"{value.magnitude:.{decimal_places}f} {value.units}"


class EnhancedMeasurement(ConversionMixin, ValidatedMeasurement):
    class Meta:
        proxy = True
```

Use `EnhancedMeasurement` anywhere you need conversion and validation together:

```python
m = EnhancedMeasurement.objects.first()
m.to_unit("kilometer")       # Quantity with rounded magnitude
m.get_all_units()             # Dict of all unit_choices conversions
m.format_value("mile", 4)    # "0.6214 mile"
```

## Handling Conversion Errors Safely

Define specific exception types and a handler class to keep error recovery consistent across your project:

```python
from django.core.exceptions import ValidationError
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MeasurementError(Exception):
    """Base exception for measurement errors"""


class UnitConversionError(MeasurementError):
    """Error for unit conversion issues"""


class MeasurementHandler:
    """Handler for safe measurement operations"""

    @staticmethod
    def safe_convert(value, target_unit: str) -> Optional[ureg.Quantity]:
        """Safely convert between units"""
        try:
            quantity = value.quantity if hasattr(value, "quantity") else value
            return quantity.to(target_unit)
        except Exception as e:
            raise UnitConversionError(
                f"Could not convert {value} to {target_unit}: {str(e)}"
            )

    @staticmethod
    def safe_create(value: float | int | Decimal, unit: str) -> ureg.Quantity:
        """Safely create a quantity"""
        try:
            return ureg.Quantity(value, unit)
        except Exception as e:
            raise MeasurementError(
                f"Could not create quantity with {value} {unit}: {str(e)}"
            )


class SafeMeasurement(models.Model):
    value = DecimalPintField("meter", display_decimal_places=2)

    def convert_value(self, target_unit: str) -> Optional[ureg.Quantity]:
        """Safely convert measurement value"""
        if self.value is None:
            return None

        try:
            return MeasurementHandler.safe_convert(self.value.quantity, target_unit)
        except UnitConversionError as e:
            logger.error(f"Conversion error: {e}")
            return None
```

This pattern returns `None` on failure instead of crashing, while still logging the underlying error for debugging.

## Handling Edge Cases

### Very Large and Very Small Quantities

When magnitudes span many orders of magnitude, scientific notation and automatic prefix selection help keep output readable.

Python's default `Decimal` context provides 28 significant digits. Values whose base-unit comparator exceeds that range (for example, converting nanometers to meters multiplies by 10^-9, consuming 9 digits of headroom) can lose precision silently. If your application mixes very large and very small quantities, raise the precision with `DJANGO_PINT_FIELD_DECIMAL_PRECISION` in your settings. See [Configuration](configuration) for details.

```python
from decimal import Decimal
from django_pint_field.models import DecimalPintField
from typing import Optional


class ExtremeMeasurement(models.Model):
    """Model for handling extreme values"""

    value = DecimalPintField(
        default_unit="meter",
        display_decimal_places=15,
    )

    def format_scientific(self, decimal_places: int = 2) -> str:
        """Format in scientific notation"""
        if self.value is None:
            return ""

        magnitude = self.value.magnitude
        if isinstance(magnitude, Decimal):
            return f"{magnitude:.{decimal_places}E} {self.value.units}"
        return str(self.value)

    def get_human_readable(self) -> str:
        """Get human-readable format with appropriate unit prefix"""
        if self.value is None:
            return ""

        prefixes = [
            ("femto", 1e-15),
            ("pico", 1e-12),
            ("nano", 1e-9),
            ("micro", 1e-6),
            ("milli", 1e-3),
            ("", 1),
            ("kilo", 1e3),
            ("mega", 1e6),
            ("giga", 1e9),
            ("tera", 1e12),
            ("peta", 1e15),
        ]

        magnitude = float(self.value.magnitude)
        base_unit = str(self.value.units)

        for prefix, scale in reversed(prefixes):
            if abs(magnitude) >= scale:
                converted = magnitude / scale
                return f"{converted:.2f} {prefix}{base_unit}"

        return str(self.value)
```

### Zero and Negative Values

When your domain requires non-negative or non-zero quantities, validate in `clean()`:

```python
from django.core.exceptions import ValidationError


class SignAwareMeasurement(models.Model):
    """Model handling zero and negative values"""

    value = DecimalPintField(
        "meter",
        display_decimal_places=2,
    )

    def clean(self) -> None:
        """Validate sign-specific constraints"""
        super().clean()

        if self.value is not None:
            self.validate_sign(self.value.magnitude)

    @staticmethod
    def validate_sign(value: Decimal) -> None:
        """Validate value sign"""
        if value < 0:
            raise ValidationError("Negative values not allowed")
        if value == 0:
            raise ValidationError("Zero values not allowed")

    def get_absolute(self) -> Optional[ureg.Quantity]:
        """Get absolute value"""
        if self.value is None:
            return None

        magnitude = abs(self.value.magnitude)
        return ureg.Quantity(magnitude, self.value.units)

    def get_sign(self) -> Optional[int]:
        """Get value sign: 1, -1, or 0"""
        if self.value is None:
            return None

        if self.value.magnitude > 0:
            return 1
        elif self.value.magnitude < 0:
            return -1
        return 0
```

## Converting Between Unit Systems

Store values in both metric and imperial, and convert freely between them:

```python
from decimal import Decimal
from django_pint_field.units import ureg


class UnitSystemConverter(models.Model):
    metric_value = DecimalPintField(
        "meter",
        display_decimal_places=2,
        unit_choices=[
            "millimeter",
            "centimeter",
            "meter",
            "kilometer",
        ],
    )
    imperial_value = DecimalPintField(
        "inch",
        display_decimal_places=2,
        unit_choices=["inch", "foot", "yard", "mile"],
    )

    def convert_to_imperial(self):
        """Convert metric value to imperial"""
        if self.metric_value:
            self.imperial_value = self.metric_value.quantity.to("inch")

    def convert_to_metric(self):
        """Convert imperial value to metric"""
        if self.imperial_value:
            self.metric_value = self.imperial_value.quantity.to("meter")

    def get_all_conversions(self):
        """Get value in all available units"""
        if self.metric_value:
            base_value = self.metric_value.quantity
        elif self.imperial_value:
            base_value = self.imperial_value.quantity
        else:
            return None
        return {
            "metric": {
                "mm": base_value.to("millimeter").magnitude,
                "cm": base_value.to("centimeter").magnitude,
                "m": base_value.to("meter").magnitude,
                "km": base_value.to("kilometer").magnitude,
            },
            "imperial": {
                "in": base_value.to("inch").magnitude,
                "ft": base_value.to("foot").magnitude,
                "yd": base_value.to("yard").magnitude,
                "mi": base_value.to("mile").magnitude,
            },
        }

    def round_conversion(self, value, decimals=2):
        """Round converted values to specified decimal places"""
        return (
            Decimal(str(value.magnitude)).quantize(Decimal(10) ** -decimals)
            * value.units
        )
```

Usage:

```python
converter = UnitSystemConverter(metric_value=ureg.Quantity("5.0 * kilometer"))
converter.convert_to_imperial()
print(converter.imperial_value)  # 196850.39... inch

conversions = converter.get_all_conversions()
# conversions["metric"]["km"] -> 5.0
# conversions["imperial"]["mi"] -> 3.1068...
```

---

## Cross-References

- See [API Reference](reference) for the full list of field parameters
- See [Cheatsheet](cheatsheet) for quick syntax examples
