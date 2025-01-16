# Usage Guide

## 1. Getting Started

### 1.1 Installation

django-pint-field requires PostgreSQL as your database backend and Django 4.2 or higher. Follow these steps to get started:

#### Install the Package

```bash
pip install django-pint-field
```

#### Add to INSTALLED_APPS

Add django-pint-field to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django_pint_field",
    # ...
]
```

#### Run Migrations

```bash
python manage.py migrate django_pint_field
```

```{caution}
Failure to run django-pint-field migrations before running migrations for models using PintFields will result in errors. The migration creates a required composite type in your PostgreSQL database.

Previous versions of the package added three composite types to the database. The newest migration modifies the columns with these types to use a single composite type.
```

#### Tips for Upgrading from Legacy django-pint-field

```{warning}
If using [django-pgtrigger](https://django-pgtrigger.readthedocs.io/en/latest/commands/) or other packages that depend on it (e.g.: django-pghistory), we highly recommend that you temporarily uninstall all triggers before running the django-pint-field migrations. It is also a good practice to make a backup of your database before running the migration. Users freshly installing `django-pint-field` do not need to worry about this warning.
```

```bash
python manage.py pgtrigger uninstall
```

Then run the migrations:

```bash
python manage.py migrate django_pint_field
```

Reinstall the triggers after the migrations are complete:

```bash
python manage.py pgtrigger install
```

### 1.2 Basic Configuration

django-pint-field provides several configuration options that can be set in your project's `settings.py` file.

#### Custom Unit Registry Setup

By default, django-pint-field uses [Pint's](https://pint.readthedocs.io/en/stable/) default unit registry. You can create and configure your own unit registry with custom units:

```python
# settings.py
from pint import UnitRegistry
from decimal import Decimal

# Create custom registry with Decimal support
custom_ureg = UnitRegistry(non_int_type=Decimal)

# Add custom units
custom_ureg.define("serving = [serving]")
custom_ureg.define("piece = [piece]")
custom_ureg.define("dozen = 12 * piece")

# Set as the unit registry for django-pint-field
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
```

#### Setting Decimal Precision

You can control the [decimal precision](https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision) used throughout your project:

```python
# settings.py

# Set to 0 or omit to use Python's default decimal precision (usually 28)
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 0

# Or set to a specific precision value
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 40
```

#### Available Settings

| Setting                               | Type         | Default               | Description                                                             |
| ------------------------------------- | ------------ | --------------------- | ----------------------------------------------------------------------- |
| `DJANGO_PINT_FIELD_UNIT_REGISTER`     | UnitRegistry | `pint.UnitRegistry()` | The unit registry to use throughout your project                        |
| `DJANGO_PINT_FIELD_DECIMAL_PRECISION` | int          | 0                     | Project-wide decimal precision. If > 0, sets Python's decimal precision |
| `DJANGO_PINT_FIELD_DEFAULT_FORMAT`    | str          | "D"                   | Default format for displaying Quantity objects                          |

#### Quick Start Example

Here's a complete example showing how to set up a model with a PintField:

```python
# models.py
from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        default_unit="gram",  # default unit
        unit_choices=[
            ("Gram", "gram"),
            ("Kilogram", "kilogram"),
            ("Pound", "pound"),
        ],  # optional
        blank=True,  # optional
        null=True,  # optional
        display_decimal_places=2,  # optional
        rounding_method="ROUND_HALF_UP",  # optional
    )

    def __str__(self):
        return f"{self.name} ({self.weight})"
```

```python
# views.py
from decimal import Decimal
from django_pint_field.units import ureg
from .models import Product

# Create a product
Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(Decimal("500"), "gram"),
)

# Query products
heavy_products = Product.objects.filter(
    weight__gte=ureg.Quantity(
        Decimal("1"),
        "kilogram",
    )
)
```

#### Verifying Installation

To verify that django-pint-field is properly installed and configured:

1. Check that the migration has been applied:

```bash
python manage.py showmigrations django_pint_field
```

2. Verify the composite type in PostgreSQL:

Start by using the psql tool, or directly from django you can use db_shell:

```bash
python manage.py dbshell
```

Then run:

```sql
\dT+ pint_field
```

3. Test a simple model:

```python
from decimal import Decimal
from django.core.management import call_command
from django_pint_field.units import ureg

# Create and test a model with a PintField
from myapp.models import Product

# Should work without errors
Product.objects.create(
    name="Test Product",
    weight=ureg.Quantity(Decimal("100"), "gram"),
)
```

4. Verify unit conversion functionality:

```python
product = Product.objects.get(name="Test Product")
print(product.weight.quantity.to("kilogram"))  # Should show 0.1 kilogram
print(product.weight.kilogram)  # Alternate method. Should show 0.1 kilogram
```

## 2. Model Fields

django-pint-field provides specialized model fields for handling physical quantities with units. These fields leverage PostgreSQL's composite type capabilities to store and manage unit-aware values efficiently.

### 2.1 Available Field Types

#### IntegerPintField

```python
from django_pint_field.models import IntegerPintField


class Product(models.Model):
    weight = IntegerPintField("gram")
```

- Stores magnitude as integer
- Best for: Measurements where users would expect to input and see whole numbers
- Supports all standard Django integer field operations
- Internally, stored as a decimal, but displayed as an integer

#### BigIntegerPintField (Deprecated)

- Note: This field is deprecated as IntegerPintField now provides the same functionality

#### DecimalPintField

```python
from django_pint_field.models import DecimalPintField


class ChemicalSample(models.Model):
    mass = DecimalPintField(
        "gram",
        display_decimal_places=4,
        rounding_method="ROUND_HALF_UP",
    )
```

- Stores magnitude as decimal
- Best for: Precise measurements requiring decimal places
- Supports advanced decimal handling features:
  - Customizable display precision
  - Configurable rounding methods
  - Automatic unit conversion

### 2.2 Field Parameters

#### Required Parameters

All PintFields require a default unit:

```python
class Product(models.Model):
    weight = IntegerPintField(
        default_unit="gram",  # default unit as string
    )
```

Alternate syntax, with the display value, and the unit as a list or tuple:

```python
class Product(models.Model):
    weight = IntegerPintField(
        default_unit=["Gram", "gram"],  # default unit as list/tuple
    )
```

#### Optional Parameters

Unit choices can be specified to limit available units. The default unit can be included in the choices list, but will be added internally even if not specified in the list.

```python
class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        unit_choices=["gram", "kilogram", "pound"],  # Optional: limit available units
        null=True,  # Optional: allow NULL in database
        blank=True,  # Optional: allow blank in forms
        help_text="Product weight",  # Optional: help text for forms
        verbose_name="Weight",  # Optional: field label
        display_decimal_places=2,  # Optional: decimal places for display
        rounding_method="ROUND_HALF_UP",  # Optional: rounding behavior
    )
```

Like default_unit, unit_choices can be specified as a string or a list/tuple. The list/tuple format allows you to specify both the display value and the unit string.

```python
unit_choices = (
    [  # List or tuple
        "gram",  # Each nested item is a string or a 2-list/2-tuple
        ("Kilogram", "kilogram"),
        ["Pound", "pound"],
    ],
)
```

##### Special DecimalPintField Parameters

```python
from decimal import ROUND_HALF_UP


class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,  # Optional: specify decimal places for display
        rounding_method=ROUND_HALF_UP,  # Optional: specify rounding behavior
    )
```

Available rounding methods:

- `ROUND_CEILING`: Round towards Infinity
- `ROUND_DOWN`: Round towards zero
- `ROUND_FLOOR`: Round towards -Infinity
- `ROUND_HALF_DOWN`: Round to nearest with ties going towards zero
- `ROUND_HALF_EVEN`: Round to nearest with ties going to nearest even integer
- `ROUND_HALF_UP`: Round to nearest with ties going away from zero
- `ROUND_UP`: Round away from zero
- `ROUND_05UP`: Round away from zero if last digit after rounding towards zero would have been 0 or 5

### 2.3 Basic Model Examples

#### Simple Model Definition

```python
from django.db import models
from django_pint_field.models import DecimalPintField


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )

    def __str__(self):
        return f"{self.name} ({self.weight})"
```

#### Model with Multiple PintFields

```python
class Package(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "kilogram",
        display_decimal_places=2,
        help_text="Package weight",
    )
    length = DecimalPintField(
        "meter",
        display_decimal_places=2,
        help_text="Package length",
    )
    width = DecimalPintField(
        "meter",
        display_decimal_places=2,
        help_text="Package width",
    )
    height = DecimalPintField(
        "meter",
        display_decimal_places=2,
        help_text="Package height",
    )

    def volume(self):
        """Calculate package volume in cubic meters"""
        return self.length * self.width * self.height
```

#### Model with Dimensional Validation

```python
from django.core.exceptions import ValidationError


class ShippingContainer(models.Model):
    name = models.CharField(max_length=100)
    volume = DecimalPintField(
        "cubic_meter",
        display_decimal_places=2,
        unit_choices=[
            ("Cubic Meter", "cubic_meter"),
            ("Cubic Foot", "cubic_foot"),
            ("Liter", "liter"),
        ],
    )

    def clean(self):
        super().clean()
        # Example of custom validation
        if self.volume and self.volume.to("cubic_meter").magnitude < 0:
            raise ValidationError({"volume": "Volume cannot be negative"})
        if self.volume and self.volume.to("cubic_meter").magnitude > 100:
            raise ValidationError({"volume": "Volume cannot exceed 100 cubic meters"})
```

## 3. Working with Quantities

### 3.1 Creating and Saving

#### Creating Model Instances

There are several ways to create model instances with PintFields, ensuring proper Decimal handling:

```python
from decimal import Decimal
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )


# Method 1: Using Decimal with Pint Quantity
product1 = Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(Decimal("500.00"), "gram"),
)

# Method 2: Using string notation with Decimal precision
product2 = Product.objects.create(
    name="Sugar",
    weight=ureg.Quantity("750.000 gram"),
)

# Method 3: Using Decimal in a tuple
product3 = Product(
    name="Salt",
    weight=(Decimal("250.00"), "gram"),
)
product3.save()

# Method 4: Using Decimal string directly
product4 = Product.objects.create(
    name="Pepper",
    weight="300.00 gram"
)
```

#### Setting Quantity Values

You can modify quantity values while maintaining Decimal precision:

```python
# Update using Decimal with Quantity object
product.weight = ureg.Quantity(Decimal("300.00"), "gram")

# Update using Decimal string
product.weight = "0.300 kilogram"

# Update using Decimal tuple
product.weight = (Decimal("400.00"), "gram")

# Update with automatic Decimal conversion
product.weight = 500  # Will be converted to Decimal(500)
product.weight = 0.75  # Will be converted to Decimal('0.75')

# Save changes
product.save()
```

#### Converting Between Units with Decimal Precision

```python
class Recipe(models.Model):
    name = models.CharField(max_length=100)
    ingredient_weight = DecimalPintField(
        "gram",
        display_decimal_places=4,
        unit_choices=["gram", "kilogram", "ounce", "pound"],
    )

    def get_weight_in_preferred_unit(self, unit="gram", precision=4):
        """Convert weight to preferred unit with specified precision"""
        if self.ingredient_weight:
            quantity = self.ingredient_weight.to(unit)
            return quantity.magnitude.quantize(Decimal(f"0.{'0' * precision}"))
        return None
```

### 3.2 Retrieving and Querying

#### Basic Field Access with Decimal Handling

```python
# Get the Quantity object with Decimal magnitude
weight = product.weight  # e.g., 500.00 gram

# Access Decimal magnitude
magnitude = product.weight.magnitude  # Decimal('500.00')

# Access units
units = product.weight.units  # e.g., gram

# String representation with Decimal precision
weight_str = str(product.weight)  # e.g., "500.00 gram"

# Formatted output
formatted_weight = f"{product.weight.magnitude:.2f} {product.weight.units}"
```

#### Accessing Magnitude and Units with Decimal Precision

```python
class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )

    def get_weight_components(self, precision=2):
        """Return magnitude and units with specified precision"""
        if not self.weight:
            return None

        magnitude = self.weight.magnitude.quantize(Decimal(f"0.{'0' * precision}"))
        return {
            "magnitude": magnitude,
            "units": str(self.weight.units),
            "base_magnitude": self.weight.to_base_units().magnitude,
        }

    def is_heavy(self, threshold=Decimal("1.0")):
        """Example of comparing quantities with Decimal precision"""
        return self.weight.to("kilogram").magnitude > threshold

    @property
    def weight_formatted(self):
        """Format weight with field's display precision"""
        if self.weight:
            return f"{self.weight.magnitude:.{self.weight.display_decimal_places}f} {self.weight.units}"
        return "No weight specified"
```

#### Unit Conversion Methods with Decimal Precision

```python
# Direct conversion with Decimal precision
kilos = product.weight.to("kilogram")  # Returns Quantity with Decimal magnitude

# Multiple conversions with consistent precision
def get_conversions(quantity, units, precision=4):
    """Convert quantity to multiple units with specified precision"""
    return {
        unit: quantity.to(unit).magnitude.quantize(Decimal(f"0.{'0' * precision}"))
        for unit in units
    }

# Usage:
conversions = get_conversions(
    product.weight,
    ["kilogram", "pound", "ounce"],
    precision=2
)

# Conversion with formatting
def format_weight(quantity, unit, precision=None):
    """Convert and format a weight quantity"""
    converted = quantity.to(unit)
    if precision is None:
        precision = quantity.display_decimal_places
    return f"{converted.magnitude:.{precision}f} {converted.units}"

# Usage:
formatted = format_weight(product.weight, "kilogram", 3)
```

### 3.3 Field Properties

#### Available Unit Conversions with Decimal Precision

Fields automatically provide conversion properties with proper Decimal handling:

```python
class WeightMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=4,
    )

    def get_all_conversions(self, precision=4):
        """Get all common mass unit conversions with specified precision"""
        if not self.weight:
            return {}

        return {
            unit: self.weight.to(unit).magnitude.quantize(Decimal(f"0.{'0' * precision}"))
            for unit in ["gram", "kilogram", "milligram", "pound", "ounce"]
        }


# Access built-in conversion properties with Decimal precision
measurement = WeightMeasurement.objects.first()
kg_value = measurement.weight__kilogram  # Returns Decimal value
gram_value = measurement.weight__gram    # Returns Decimal value
```

#### Validation Behavior with Decimal Precision

PintFields include built-in validation with Decimal precision handling:

```python
class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
        unit_choices=["gram", "kilogram"],
    )

    def clean(self):
        super().clean()
        if self.weight:
            # Dimensionality validation (automatic)
            # Would raise ValidationError if assigning a length unit
            #   instead of a weight, for instance

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

            # Precision validation (automatic for DecimalPintField)
            # Will raise ValidationError if exceeds display_decimal_places
```

## 4. Querying and Filtering

### 4.1 Available Lookups

django-pint-field supports the following lookup types with proper Decimal handling:

#### Exact Match

```python
from decimal import Decimal
from django_pint_field.units import ureg

# Find products weighing exactly 500 grams
Product.objects.filter(weight__exact=ureg.Quantity(Decimal("500.00"), "gram"))

# Shorthand syntax with Decimal precision
Product.objects.filter(weight=ureg.Quantity("500.00 gram"))
```

#### Greater Than / Less Than

```python
# Greater than (gt) with Decimal
Product.objects.filter(weight__gt=ureg.Quantity(Decimal("1.000"), "kilogram"))

# Greater than or equal to (gte)
Product.objects.filter(weight__gte=ureg.Quantity("1.000 kilogram"))

# Less than (lt) with Decimal precision
Product.objects.filter(weight__lt=ureg.Quantity(Decimal("500.00"), "gram"))

# Less than or equal to (lte)
Product.objects.filter(weight__lte=ureg.Quantity("500.00 gram"))
```

#### Range

```python
# Find products within a weight range with Decimal precision
min_weight = ureg.Quantity(Decimal("100.00"), "gram")
max_weight = ureg.Quantity(Decimal("1.000"), "kilogram")
Product.objects.filter(
    weight__range=(min_weight, max_weight),
)
```

#### Null Checks

```python
# Find products with no weight specified
Product.objects.filter(weight__isnull=True)

# Find products with weight specified
Product.objects.filter(weight__isnull=False)
```

### 4.2 Query Examples

#### Basic Filtering with Decimal Precision

```python
from decimal import Decimal
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )


# Simple equality with Decimal
light_products = Product.objects.filter(
    weight=ureg.Quantity(Decimal("100.00"), "gram"),
)

# Comparison with different units (automatically converted)
heavy_products = Product.objects.filter(
    weight__gte=ureg.Quantity(Decimal("1.000"), "kilogram"),
)

# Multiple conditions with Decimal precision
medium_products = Product.objects.filter(
    weight__gt=ureg.Quantity(Decimal("250.00"), "gram"),
    weight__lt=ureg.Quantity(Decimal("750.00"), "gram"),
)

# Combining with OR conditions
from django.db.models import Q

mixed_products = Product.objects.filter(
    Q(weight__lt=ureg.Quantity(Decimal("100.00"), "gram"))
    | Q(
        weight__gt=ureg.Quantity(Decimal("1.000"), "kilogram"),
    )
)
```

#### Range Queries with Decimal Handling

```python
class ShippingRate(models.Model):
    min_weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )
    max_weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )


# Find applicable shipping rate for a package with Decimal precision
def get_shipping_rate(package_weight):
    return ShippingRate.objects.filter(
        min_weight__lte=package_weight,
        max_weight__gt=package_weight,
    ).first()


# Find overlapping weight ranges with Decimal handling
def find_overlapping_rates():
    return ShippingRate.objects.filter(
        min_weight__lt=models.F("max_weight"),
    ).exclude(
        max_weight__lte=models.F("min_weight"),
    )
```

#### Complex Queries with Decimal Precision

```python
from decimal import Decimal
from django.db.models import F, ExpressionWrapper, DecimalField


class Shipment(models.Model):
    actual_weight = DecimalPintField(
        "kilogram",
        display_decimal_places=3,
    )
    volume = DecimalPintField(
        "cubic_meter",
        display_decimal_places=4,
    )

    @property
    def volumetric_weight(self):
        """Calculate volumetric weight: volume * mass"""
        if self.volume:
            return self.volume * ureg.gram
        return None

    @classmethod
    def get_overweight_shipments(cls):
        """Find shipments where actual weight exceeds volumetric weight"""
        return cls.objects.filter(
            actual_weight__gt=F("volume") * ureg.gram,
        )

    @classmethod
    def get_shipments_by_weight_category(cls):
        """Categorize shipments by weight ranges with Decimal precision"""
        categories = {
            "light": (Decimal("0.000"), Decimal("10.000")),  # kg
            "medium": (Decimal("10.000"), Decimal("50.000")),
            "heavy": (Decimal("50.000"), Decimal("100.000")),
            "extra_heavy": (Decimal("100.000"), None),
        }

        queries = []
        for category, (min_weight, max_weight) in categories.items():
            q = Q()
            if min_weight is not None:
                q &= Q(actual_weight__gte=ureg.Quantity(min_weight, "kilogram"))
            if max_weight is not None:
                q &= Q(actual_weight__lt=ureg.Quantity(max_weight, "kilogram"))
            queries.append((category, q))

        return {
            category: cls.objects.filter(query).count() for category, query in queries
        }
```

### 4.3 Limitations and Considerations

#### Unsupported Lookups

The following lookups are intentionally disabled and will raise `PintFieldLookupError`:

- `contains`
- `date`
- `day`
- `endswith`
- `hour`
- `icontains`
- `iendswith`
- `in`
- `iregex`
- `isearch`
- `iso_week_day`
- `iso_year`
- `istartswith`
- `minute`
- `month`
- `quarter`
- `regex`
- `search`
- `second`
- `startswith`
- `time`
- `week`
- `week_day`
- `year`

#### Performance Considerations with Decimal Handling

```python
class InventoryItem(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )

    class Meta:
        indexes = [
            models.Index(fields=["weight"]),  # Indexes the composite field
        ]

    @classmethod
    def bulk_convert_weights(cls, unit="kilogram", precision=3):
        """Efficient bulk conversion of weights with Decimal precision"""
        items = cls.objects.all()
        # Use iterator() for large querysets to reduce memory usage
        for item in items.iterator():
            converted_weight = item.weight.to(unit)
            formatted_weight = converted_weight.magnitude.quantize(
                Decimal(f"0.{'0' * precision}")
            )
            print(f"Original: {item.weight}, Converted: {formatted_weight} {unit}")
```

#### Unit Compatibility with Decimal Precision

```python
from django.core.exceptions import ValidationError


class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )
    size = DecimalPintField(
        "meter",
        display_decimal_places=3,
    )

    def clean(self):
        super().clean()
        # Cannot compare incompatible units
        try:
            if self.weight and self.size:
                # This will raise an exception:
                if self.weight > self.size:
                    pass
        except:
            raise ValidationError("Cannot compare weight and size units")

    @classmethod
    def safe_weight_comparison(cls, weight1, weight2):
        """Safely compare two weight quantities with Decimal precision"""
        try:
            # Use the comparator, which is always in base units
            # Will not raise an exception:
            return base_weight1.comparator < base_weight2.comparator
        except:
            raise ValidationError("Incompatible units for comparison")
```

#### Best Practices for Querying with Decimal Handling

```python
class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        display_decimal_places=2,
    )

    @classmethod
    def get_by_weight_range(cls, min_weight, max_weight, unit="gram", precision=2):
        """
        Safely query by weight range with unit conversion and Decimal precision

        Args:
            min_weight: Numeric minimum weight
            max_weight: Numeric maximum weight
            unit: Unit string (default: 'gram')
            precision: Decimal places for comparison
        """
        try:
            min_q = ureg.Quantity(
                Decimal(min_weight).quantize(Decimal(f"0.{'0' * precision}")), unit
            )
            max_q = ureg.Quantity(
                Decimal(max_weight).quantize(Decimal(f"0.{'0' * precision}")), unit
            )

            return cls.objects.filter(weight__gte=min_q, weight__lte=max_q)
        except Exception as e:
            raise ValidationError(f"Invalid weight range: {str(e)}")

    @classmethod
    def get_weight_distribution(cls, ranges, unit="kilogram", precision=3):
        """
        Get count of products in each weight range with Decimal precision

        Args:
            ranges: List of (min, max) tuples in specified unit
            unit: Unit string for the ranges
            precision: Decimal places for range boundaries
        """
        distribution = {}
        for min_val, max_val in ranges:
            min_dec = Decimal(min_val).quantize(Decimal(f"0.{'0' * precision}"))
            max_dec = Decimal(max_val).quantize(Decimal(f"0.{'0' * precision}"))
            count = cls.get_by_weight_range(min_dec, max_dec, unit, precision).count()
            distribution[f"{min_dec}-{max_dec} {unit}"] = count
        return distribution
```

## 5. Aggregation Operations

### 5.1 Available Aggregates

django-pint-field provides a comprehensive set of aggregate functions that work seamlessly with PintFields while maintaining unit awareness and proper decimal handling:

#### PintAvg

Calculates the average value, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintAvg

# Calculate average weight with decimal precision
avg_weight = Product.objects.aggregate(avg_weight=PintAvg("weight"))
```

#### PintCount

Counts the number of non-null values, returning an Integer.

```python
from django_pint_field.aggregates import PintCount

# Count products with weight specified
weight_count = Product.objects.aggregate(weight_count=PintCount("weight"))
```

#### PintMax

Returns the maximum value, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintMax

# Find heaviest product weight with decimal precision
max_weight = Product.objects.aggregate(max_weight=PintMax("weight"))
```

#### PintMin

Returns the minimum value, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintMin

# Find lightest product weight with decimal precision
min_weight = Product.objects.aggregate(min_weight=PintMin("weight"))
```

#### PintStdDev

Calculates the standard deviation, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintStdDev

# Calculate weight standard deviation with decimal precision
std_dev = Product.objects.aggregate(std_dev=PintStdDev("weight"))

# With sample parameter for sample standard deviation
sample_std_dev = Product.objects.aggregate(
    std_dev=PintStdDev("weight", sample=True),
)
```

#### PintSum

Calculates the sum of values, returning a Quantity with proper decimal handling.

```python
from django_pint_field.aggregates import PintSum

# Calculate total weight with decimal precision
total_weight = Product.objects.aggregate(total_weight=PintSum("weight"))
```

#### PintVariance

Calculates the variance, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintVariance

# Calculate weight variance with decimal precision
variance = Product.objects.aggregate(variance=PintVariance("weight"))

# With sample parameter for sample variance
sample_variance = Product.objects.aggregate(
    variance=PintVariance("weight", sample=True)
)
```

### 5.2 Usage Examples

#### Simple Aggregations with Decimal Precision

```python
from decimal import Decimal
from django_pint_field.aggregates import PintAvg, PintCount, PintMax, PintMin, PintSum
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        default_unit="gram",
        display_decimal_places=2,  # Control display precision
        rounding_method="ROUND_HALF_UP",  # Set rounding strategy
    )

    @classmethod
    def get_weight_statistics(cls):
        """Get comprehensive weight statistics with proper decimal handling"""
        stats = cls.objects.aggregate(
            total_weight=PintSum("weight"),
            average_weight=PintAvg("weight"),
            min_weight=PintMin("weight"),
            max_weight=PintMax("weight"),
            product_count=PintCount("weight"),
        )

        return {
            "total": stats["total_weight"].to("kilogram"),
            "average": stats["average_weight"].to("gram"),
            "min": stats["min_weight"].to("gram"),
            "max": stats["max_weight"].to("kilogram"),
            "count": stats["product_count"],
        }
```

#### Combining Aggregates with Unit Conversion

```python
class Shipment(models.Model):
    weight = DecimalPintField(
        default_unit="kilogram",
        display_decimal_places=2,
    )
    volume = DecimalPintField(
        default_unit="cubic_meter",
        display_decimal_places=3,
    )

    @classmethod
    def get_shipping_metrics(cls):
        """Calculate multiple metrics with proper unit handling"""
        metrics = cls.objects.aggregate(
            total_weight=PintSum("weight"),
            avg_weight=PintAvg("weight"),
            total_volume=PintSum("volume"),
            avg_volume=PintAvg("volume"),
            shipment_count=PintCount("id"),
        )

        # Calculate density with proper unit handling
        if metrics["shipment_count"] > 0:
            total_weight_kg = metrics["total_weight"].to("kilogram")
            total_volume_m3 = metrics["total_volume"].to("cubic_meter")
            avg_density = (total_weight_kg / total_volume_m3).to("kg/m³")
        else:
            avg_density = ureg.Quantity(0, "kg/m³")

        return {
            **metrics,
            "average_density": avg_density,
        }
```

#### Advanced Aggregation with Decimal Precision

```python
class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_weight = DecimalPintField(
        default_unit="gram",
        display_decimal_places=2,
    )

    @classmethod
    def get_inventory_analysis(cls, output_unit="kilogram"):
        """
        Analyze inventory with custom output units and decimal precision

        Args:
            output_unit: Desired unit for weight outputs
        """
        base_stats = cls.objects.aggregate(
            total_items=models.Sum("quantity"),
            total_weight=PintSum(models.F("quantity") * models.F("unit_weight")),
            avg_unit_weight=PintAvg("unit_weight"),
            heaviest_unit=PintMax("unit_weight"),
            lightest_unit=PintMin("unit_weight"),
        )

        # Convert all weight measurements with proper decimal handling
        converted_stats = {
            "total_items": base_stats["total_items"],
            "total_weight": base_stats["total_weight"].to(output_unit),
            "avg_unit_weight": base_stats["avg_unit_weight"].to(output_unit),
            "heaviest_unit": base_stats["heaviest_unit"].to(output_unit),
            "lightest_unit": base_stats["lightest_unit"].to(output_unit),
        }

        return converted_stats
```

#### Best Practices for Aggregations

```python
from django.db import models
from django_pint_field.aggregates import (
    PintAvg, PintCount, PintMax, PintMin, PintSum, PintStdDev, PintVariance
)
from django_pint_field.units import ureg
import logging

logger = logging.getLogger(__name__)

class WeightMeasurement(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = DecimalPintField(
        default_unit="gram",
        display_decimal_places=2,
    )

    class Meta:
        indexes = [
            models.Index(fields=["weight"]),  # Indexes the composite field
        ]

    @classmethod
    def analyze_measurements(cls, start_date=None, end_date=None):
        """
        Analyze weight measurements with proper error handling,
        unit conversion, and decimal precision
        """
        queryset = cls.objects.all()

        # Apply date filtering if provided
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        try:
            stats = queryset.aggregate(
                count=PintCount("weight"),
                total=PintSum("weight"),
                average=PintAvg("weight"),
                std_dev=PintStdDev("weight"),
                variance=PintVariance("weight"),
            )

            # Convert to appropriate units based on magnitude
            if stats["average"]:
                avg_magnitude = stats["average"].to("gram").magnitude

                if avg_magnitude > 1000:
                    unit = "kilogram"
                else:
                    unit = "gram"

                stats = {
                    "count": stats["count"],
                    "total": stats["total"].to(unit),
                    "average": stats["average"].to(unit),
                    "std_dev": stats["std_dev"].to(unit),
                    "variance": stats["variance"].to(unit * unit),
                    "unit": unit,
                }

            return stats

        except Exception as e:
            logger.error(f"Error analyzing measurements: {str(e)}")
            return None
```

## 6. Forms, Widgets, and Admin

### 6.1 Form Fields

django-pint-field provides two form field types that correspond to the model fields, with enhanced support for decimal precision and unit handling:

#### IntegerPintFormField

Used with IntegerPintField and BigIntegerPintField models:

```python
from django import forms
from django_pint_field.forms import IntegerPintFormField


class ProductForm(forms.Form):
    weight = IntegerPintFormField(
        default_unit="gram",
        unit_choices=[
            ("Gram", "gram"),
            ("Kilogram", "kilogram"),
            ("Pound", "pound"),
        ],
        required=True,
        help_text="Enter the product weight in whole numbers",
        min_value=0,  # Minimum allowed value
        max_value=1000000,  # Maximum allowed value
    )
```

#### DecimalPintFormField

Used with DecimalPintField models with proper decimal handling:

```python
from decimal import Decimal
from django_pint_field.forms import DecimalPintFormField


class PreciseProductForm(forms.Form):
    weight = DecimalPintFormField(
        default_unit="gram",
        unit_choices=[
            ("Gram", "gram"),
            ("Kilogram", "kilogram"),
            ("Pound", "pound"),
        ],
        display_decimal_places=2,  # Display precision
        rounding_method="ROUND_HALF_UP",  # Rounding strategy
        required=True,
        help_text="Enter the precise weight",
        min_value=Decimal("0.01"),  # Minimum allowed value
        max_value=Decimal("1000.00"),  # Maximum allowed value
    )
```

#### Field Parameters and Options

Both form fields accept these common parameters:

```python
class WeightForm(forms.ModelForm):
    weight = DecimalPintFormField(
        default_unit="gram",  # Required: Base unit for the field
        unit_choices=[  # Optional: Available units with display names
            ("Gram", "gram"),
            ("Kilogram", "kilogram"),
            ("Pound", "pound"),
        ],
        required=True,  # Optional: Whether field is required
        label="Weight",  # Optional: Field label
        help_text="Product weight",  # Optional: Help text
        disabled=False,  # Optional: Disable field
        initial=None,  # Optional: Initial value
        widget=None,  # Optional: Custom widget
        min_value=None,  # Optional: Minimum allowed value
        max_value=None,  # Optional: Maximum allowed value
    )

    class Meta:
        model = Product
        fields = ["weight"]
```

DecimalPintFormField specific parameters:

```python
class PreciseWeightForm(forms.ModelForm):
    weight = DecimalPintFormField(
        default_unit="gram",
        display_decimal_places=2,  # Display precision
        rounding_method="ROUND_HALF_UP",  # Rounding strategy
        min_value=Decimal("0.01"),  # Minimum allowed value
        max_value=Decimal("1000.00"),  # Maximum allowed value
    )
```

### 6.2 Default Widget (PintFieldWidget)

The PintFieldWidget is the default widget for PintFields, combining a numeric input with a unit selection dropdown and enhanced decimal handling.

#### Basic Usage

```python
from django_pint_field.widgets import PintFieldWidget


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["weight"]
        widgets = {
            "weight": PintFieldWidget(
                default_unit="gram",
                unit_choices=[
                    ("Gram", "gram"),
                    ("Kilogram", "kilogram"),
                    ("Pound", "pound"),
                ],
                attrs={
                    "step": "0.01",  # Decimal precision
                },
            )
        }
```

#### Customization Options

```python
from django_pint_field.widgets import PintFieldWidget


class CustomPintWidget(PintFieldWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize the numeric input
        self.widgets[0].attrs.update(
            {
                "class": "form-control",
                "placeholder": "Enter value",
                "min": "0",
                "step": "0.01",  # Decimal precision
            }
        )

        # Customize the unit select
        self.widgets[1].attrs.update(
            {
                "class": "form-select",
            }
        )


class CustomProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["weight"]
        widgets = {
            "weight": CustomPintWidget(
                default_unit="gram",
                unit_choices=[
                    ("Gram", "gram"),
                    ("Kilogram", "kilogram"),
                    ("Pound", "pound"),
                ],
                attrs={"class": "weight-input-group"},
            )
        }
```

#### Example Implementation with Decimal Handling

```python
from decimal import Decimal
from django import forms
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.units import ureg


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure widget with decimal precision
        self.fields["weight"].widget = PintFieldWidget(
            default_unit="gram",
            unit_choices=[
                ("Gram", "gram"),
                ("Kilogram", "kilogram"),
                ("Pound", "pound"),
            ],
            attrs={
                "class": "weight-input",
                "step": "0.01",  # Decimal precision
                "data-toggle": "tooltip",
                "title": "Enter product weight",
            },
        )

    def clean_weight(self):
        """Custom validation for weight field with decimal precision"""
        weight = self.cleaned_data.get("weight")
        if weight:
            min_weight = ureg.Quantity(Decimal("0.01"), "gram")
            max_weight = ureg.Quantity(Decimal("1000.00"), "kilogram")

            if weight < min_weight:
                raise forms.ValidationError(f"Weight must be at least {min_weight}")
            if weight > max_weight:
                raise forms.ValidationError(f"Weight cannot exceed {max_weight}")
        return weight

    class Meta:
        model = Product
        fields = ["name", "weight"]
```

### 6.3 Tabled Widget (TabledPintFieldWidget)

The TabledPintFieldWidget extends the basic PintFieldWidget by adding a table showing the value converted to all available units with proper decimal handling.

#### Features and Benefits

- Real-time unit conversions with decimal precision
- Customizable display formatting
- Enhanced user experience with immediate feedback
- Configurable decimal places for display
- Responsive design support

#### Configuration Options

```python
from django_pint_field.widgets import TabledPintFieldWidget


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["weight"]
        widgets = {
            "weight": TabledPintFieldWidget(
                default_unit="gram",
                unit_choices=[
                    ("Gram", "gram"),
                    ("Kilogram", "kilogram"),
                    ("Pound", "pound"),
                ],
                floatformat=2,  # Number of decimal places in table
                table_class="conversion-table",  # CSS class for table
                td_class="text-end",  # CSS class for table cells
                show_units_in_values=True,  # Show units in value cells
            )
        }
```

#### Template Customization

The widget template can be overridden by creating a template at:
`templates/django_pint_field/tabled_django_pint_field_widget.html`

Example custom template with enhanced decimal handling:

```html
{% spaceless %}
<div class="pint-field-inputs">
  {% for widget in widget.subwidgets %}
    {% include widget.template_name %}
  {% endfor %}
</div>

{% if values_list %}
<div class="pint-field-table">
  <table class="{{ table_class }}">
    <thead>
      <tr>
        <th>Unit</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      {% for value_item in values_list %}
      <tr>
        <td>{{ value_item.units }}</td>
        <td class="{{ td_class }}">
          {{ value_item.magnitude|floatformat:floatformat }}
          {% if show_units_in_values %}
            {{ value_item.units }}
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endif %}
{% endspaceless %}
```

#### Example Implementation with Decimal Precision

```python
from decimal import Decimal
from django_pint_field.widgets import TabledPintFieldWidget


class WeightForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure tabled widget with decimal precision
        self.fields["weight"].widget = TabledPintFieldWidget(
            default_unit="gram",
            unit_choices=[
                ("Gram", "gram"),
                ("Kilogram", "kilogram"),
                ("Pound", "pound"),
            ],
            floatformat=2,  # Decimal places
            table_class="table table-striped table-hover",
            td_class="text-end",
            show_units_in_values=True,
            attrs={
                "step": "0.01",  # Input decimal precision
            },
        )

    class Meta:
        model = Product
        fields = ["name", "weight"]

    class Media:
        css = {
            "all": ["css/weight-form.css"]
        }
        js = ["js/weight-form.js"]
```

Example CSS for styling the tabled widget:

```css
/* weight-form.css */
.conversion-table {
  margin-top: 1rem;
  width: 100%;
  border-collapse: collapse;
}

.conversion-table th,
.conversion-table td {
  padding: 0.5rem;
  border: 1px solid #dee2e6;
}

.conversion-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.text-end {
  text-align: right;
}

.conversion-table tr:hover {
  background-color: #f5f5f5;
}

/* Responsive table */
@media (max-width: 768px) {
  .conversion-table {
    display: block;
    overflow-x: auto;
  }
}
```

### 6.4 Django Admin Integration

#### Basic ModelAdmin Setup

The django-pint-field package provides seamless integration with Django's admin interface. Here's how to set up and customize your admin for models with PintFields:

##### Registering Models with PintFields

(Same as any other model)

```python
from django.contrib import admin
from django_pint_field.units import ureg
from .models import WeightModel


@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight"]
    search_fields = ["name"]
    ordering = ["name"]
```

##### Default Admin Representation

PintFields are automatically rendered in the admin with their default units. However, you can customize their display:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight"]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ["weight_base_value"]
        return []

    def weight_base_value(self, obj):
        """Display the base unit value"""
        if obj.weight:
            return obj.weight.to_base_units()

    weight_base_value.short_description = "Base Weight Value"
```

##### List Display Configuration

You can display weights in multiple units using custom methods:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "weight",
        "get_weight_kg",
        "get_weight_lb",
        "get_weight_oz",
    ]

    def get_weight_kg(self, obj):
        """Display weight in kilograms"""
        if obj.weight:
            kg = obj.weight.to("kilogram")
            return f"{kg.magnitude:.2f} {kg.units}"

    get_weight_kg.short_description = "Weight (kg)"

    def get_weight_lb(self, obj):
        """Display weight in pounds"""
        if obj.weight:
            lb = obj.weight.to("pound")
            return f"{lb.magnitude:.2f} {lb.units}"

    get_weight_lb.short_description = "Weight (lb)"

    def get_weight_oz(self, obj):
        """Display weight in ounces"""
        if obj.weight:
            oz = obj.weight.to("ounce")
            return f"{oz.magnitude:.1f} {oz.units}"

    get_weight_oz.short_description = "Weight (oz)"
```

##### Using Property Shortcuts

django-pint-field provides a convenient shortcut for unit conversion using double underscores:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "weight",  # Original value
        "weight__kilogram",  # Converted to kg
        "weight__pound",  # Converted to lb
        "weight__ounce",  # Converted to oz
    ]

    list_display_links = ["name", "weight"]
```

##### Advanced List Display Configuration

```python
from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html
from django_pint_field.units import ureg


@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "formatted_weight",
        "weight_status",
        "weight__kilogram",
    ]

    def formatted_weight(self, obj):
        """Custom formatted weight display"""
        if not obj.weight:
            return "-"

        # Format based on magnitude
        magnitude = obj.weight.to("gram").magnitude
        if magnitude >= 1000:
            value = obj.weight.to("kilogram")
            color = "red"
        else:
            value = obj.weight
            color = "green"

        return format_html(
            '<span style="color: {};">{:.2f} {}</span>',
            color,
            value.magnitude,
            value.units,
        )

    formatted_weight.short_description = "Weight"
    formatted_weight.admin_order_field = "weight"

    def weight_status(self, obj):
        """Display weight status with icon"""
        if not obj.weight:
            return "-"

        threshold = ureg.Quantity("500 gram")
        if obj.weight > threshold:
            icon = "⬆️"
            text = "Heavy"
        else:
            icon = "⬇️"
            text = "Light"

        return format_html("{} {}", icon, text)

    weight_status.short_description = "Status"
```

#### Custom Admin Forms

##### Custom Admin Forms Implementation

###### Overriding Default Widgets

```python
from django import forms
from django.contrib import admin
from django_pint_field.widgets import TabledPintFieldWidget
from .models import WeightModel


class WeightModelAdminForm(forms.ModelForm):
    class Meta:
        model = WeightModel
        fields = "__all__"
        widgets = {
            "weight": TabledPintFieldWidget(
                default_unit="gram",
                unit_choices=["gram", "kilogram", "pound"],
                floatformat=2,
                table_class="admin-weight-table",
            )
        }


class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
```

###### Manually Adding Unit Conversion Displays

```python
from django.utils.html import format_html


class WeightModelAdminForm(forms.ModelForm):
    converted_weights = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = WeightModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")

        if instance and instance.weight:
            self.fields["converted_weights"].initial = self.get_conversions(
                instance.weight
            )

    def get_conversions(self, weight):
        conversions = {
            "gram": weight.to("gram"),
            "kilogram": weight.to("kilogram"),
            "pound": weight.to("pound"),
            "ounce": weight.to("ounce"),
        }
        return format_html(
            '<div class="weight-conversions">'
            '<table class="conversion-table">'
            "<tr><th>Unit</th><th>Value</th></tr>"
            "{}"
            "</table></div>",
            format_html_join(
                "\n",
                "<tr><td>{}</td><td>{:.3f}</td></tr>",
                ((unit, value.magnitude) for unit, value in conversions.items()),
            ),
        )


class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
    readonly_fields = ["converted_weights"]
```

###### Form Field Customization

```python
class WeightModelAdminForm(forms.ModelForm):
    min_weight = forms.DecimalField(required=False, disabled=True)
    max_weight = forms.DecimalField(required=False, disabled=True)

    class Meta:
        model = WeightModel
        fields = "__all__"
        widgets = {
            "weight": TabledPintFieldWidget(
                default_unit="gram",
                unit_choices=["gram", "kilogram", "pound"],
                floatformat=2,
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize weight field
        self.fields["weight"].help_text = "Enter weight in any supported unit"
        self.fields["weight"].widget.attrs.update(
            {"class": "weight-input", "data-validation": "weight"}
        )

        # Set min/max values if instance exists
        if self.instance.pk:
            category = self.instance.category
            if category:
                self.fields["min_weight"].initial = category.min_weight
                self.fields["max_weight"].initial = category.max_weight


class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
    fieldsets = (
        (None, {"fields": ("name", "category")}),
        (
            "Weight Information",
            {
                "fields": ("weight", "converted_weights"),
                "classes": ("weight-fieldset",),
                "description": "Enter and view weight in various units",
            },
        ),
        (
            "Weight Limits",
            {
                "fields": ("min_weight", "max_weight"),
                "classes": ("collapse",),
            },
        ),
    )
```

#### List Display and Filtering

##### Custom List Filters

```python
from django.contrib import admin
from django_pint_field.units import ureg


class WeightRangeFilter(admin.SimpleListFilter):
    title = "weight range"
    parameter_name = "weight_range"

    def lookups(self, request, model_admin):
        return (
            ("light", "Light (< 100g)"),
            ("medium", "Medium (100g - 1kg)"),
            ("heavy", "Heavy (> 1kg)"),
            ("very_heavy", "Very Heavy (> 10kg)"),
        )

    def queryset(self, request, queryset):
        if self.value() == "light":
            return queryset.filter(weight__lt=ureg.Quantity("100 gram"))
        elif self.value() == "medium":
            return queryset.filter(
                weight__gte=ureg.Quantity("100 gram"),
                weight__lt=ureg.Quantity("1 kilogram"),
            )
        elif self.value() == "heavy":
            return queryset.filter(
                weight__gte=ureg.Quantity("1 kilogram"),
                weight__lt=ureg.Quantity("10 kilogram"),
            )
        elif self.value() == "very_heavy":
            return queryset.filter(weight__gte=ureg.Quantity("10 kilogram"))
```

##### Unit Conversion in List Display

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight_with_conversions", "category"]
    list_filter = [WeightRangeFilter, "category"]  # Defined above

    def weight_with_conversions(self, obj):
        if not obj.weight:
            return "-"

        # Convert to common units
        in_g = obj.weight.to("gram")
        in_kg = obj.weight.to("kilogram")
        in_lb = obj.weight.to("pound")

        return format_html(
            '<div class="weight-display">'
            '<span class="primary-weight">{:.2f} {}</span>'
            '<div class="weight-conversions">'
            "<small>({:.2f} {}, {:.2f} {})</small>"
            "</div>"
            "</div>",
            obj.weight.magnitude,
            obj.weight.units,
            in_kg.magnitude,
            in_kg.units,
            in_lb.magnitude,
            in_lb.units,
        )

    weight_with_conversions.short_description = "Weight"
    weight_with_conversions.admin_order_field = "weight"

    class Media:
        css = {"all": ["admin/css/weight_display.css"]}
```

Example CSS for weight display:

```css
/* admin/css/weight_display.css */
.weight-display {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.primary-weight {
  font-weight: bold;
}

.weight-conversions {
  color: #666;
}

.conversion-table {
  margin-top: 0.5rem;
  border-collapse: collapse;
}

.conversion-table th,
.conversion-table td {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
}

.conversion-table th {
  background-color: #f5f5f5;
}
```

##### Search Functionality

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight", "category"]
    list_filter = [WeightRangeFilter, "category"]  # Defined above
    search_fields = ["name", "category__name"]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Try to parse search term as a weight
        try:
            search_quantity = ureg.Quantity(search_term)
            # Add weight-based filtering
            weight_q = Q(
                weight__gte=search_quantity.to("gram") * 0.9,
            ) & Q(
                weight__lte=search_quantity.to("gram") * 1.1,
            )
            queryset |= self.model.objects.filter(weight_q)
        except:
            pass

        return queryset, use_distinct
```

#### Admin Actions

##### Bulk Unit Conversion Actions

Remember that the underlying `comparator` on all model fields is in base units, but we can modify the magnitude and units for a set of model instances - without affecting the comparator - using this example.

```python
from django.contrib import admin
from django.contrib import messages
from django_pint_field.units import ureg


@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    actions = [
        "convert_to_kilograms",
        "convert_to_pounds",
        "standardize_units",
    ]

    @admin.action(description="Convert selected weights to kilograms")
    def convert_to_kilograms(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.weight:
                obj.weight = obj.weight.to("kilogram")
                obj.save()
                updated += 1

        self.message_user(
            request,
            f"Successfully converted {updated} weights to kilograms.",
            messages.SUCCESS,
        )

    @admin.action(description="Convert selected weights to pounds")
    def convert_to_pounds(self, request, queryset):
        updated = 0
        errors = 0

        for obj in queryset:
            try:
                if obj.weight:
                    obj.weight = obj.weight.to("pound")
                    obj.save()
                    updated += 1
            except Exception as e:
                errors += 1

        if updated:
            self.message_user(
                request,
                f"Successfully converted {updated} weights to pounds.",
                messages.SUCCESS,
            )
        if errors:
            self.message_user(
                request, f"Failed to convert {errors} weights.", messages.ERROR
            )

    @admin.action(description="Standardize units based on magnitude")
    def standardize_units(self, request, queryset):
        """Convert weights to the most appropriate unit based on magnitude"""
        updated = 0

        for obj in queryset:
            if not obj.weight:
                continue

            # Convert to grams to check magnitude
            weight_in_g = obj.weight.to("gram")
            magnitude = weight_in_g.magnitude

            # Choose appropriate unit
            if magnitude >= 1_000_000:  # 1,000 kg
                new_unit = "metric_ton"
            elif magnitude >= 1_000:  # 1 kg
                new_unit = "kilogram"
            elif magnitude >= 1:  # 1 g
                new_unit = "gram"
            else:
                new_unit = "milligram"

            obj.weight = obj.weight.to(new_unit)
            obj.save()
            updated += 1

        self.message_user(
            request,
            f"Successfully standardized units for {updated} weights.",
            messages.SUCCESS,
        )
```

##### Export with Specific Units

```python
import csv
from django.http import HttpResponse


class WeightModelAdmin(admin.ModelAdmin):
    actions = ["export_as_csv"]

    @admin.action(description="Export selected items to CSV")
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(meta)
        writer = csv.writer(response)

        # Write header with unit specifications
        header = field_names + ["weight_kg", "weight_lb", "weight_g"]
        writer.writerow(header)

        # Write data rows
        for obj in queryset:
            row_data = [getattr(obj, field) for field in field_names]

            # Add weight in different units
            if obj.weight:
                row_data.extend(
                    [
                        obj.weight.to("kilogram").magnitude,
                        obj.weight.to("pound").magnitude,
                        obj.weight.to("gram").magnitude,
                    ]
                )
            else:
                row_data.extend(["", "", ""])

            writer.writerow(row_data)

        return response
```

##### Mass Update Actions

```python
from django import forms
from django.contrib.admin import helpers
from django.template.response import TemplateResponse


class MassWeightUpdateForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    conversion_unit = forms.ChoiceField(
        choices=[
            ("gram", "Grams"),
            ("kilogram", "Kilograms"),
            ("pound", "Pounds"),
        ],
        required=True,
    )
    adjustment_factor = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=1.0,
        help_text="Multiply current weights by this factor",
    )


class WeightModelAdmin(admin.ModelAdmin):
    actions = ["mass_weight_update"]

    @admin.action(description="Mass update weights")
    def mass_weight_update(self, request, queryset):
        form = None

        if "apply" in request.POST:
            form = MassWeightUpdateForm(request.POST)

            if form.is_valid():
                conversion_unit = form.cleaned_data["conversion_unit"]
                adjustment_factor = form.cleaned_data["adjustment_factor"]

                updated = 0
                errors = 0

                for obj in queryset:
                    try:
                        if obj.weight:
                            # Convert to desired unit
                            converted = obj.weight.to(conversion_unit)
                            # Apply adjustment factor
                            adjusted = converted.magnitude * adjustment_factor
                            # Create new quantity
                            obj.weight = ureg.Quantity(adjusted, conversion_unit)
                            obj.save()
                            updated += 1
                    except Exception as e:
                        errors += 1

                # Message user about the results
                if updated:
                    self.message_user(
                        request,
                        f"Successfully updated {updated} weights.",
                        messages.SUCCESS,
                    )
                if errors:
                    self.message_user(
                        request, f"Failed to update {errors} weights.", messages.ERROR
                    )
                return None

        if not form:
            form = MassWeightUpdateForm(
                initial={
                    "_selected_action": request.POST.getlist(
                        helpers.ACTION_CHECKBOX_NAME
                    )
                }
            )

        context = {
            "title": "Mass Update Weights",
            "form": form,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "queryset": queryset,
            "opts": self.model._meta,
        }

        return TemplateResponse(request, "admin/mass_weight_update.html", context)
```

Template for mass update (`admin/mass_weight_update.html`):

```html
{% extends "admin/base_site.html" %} {% block content %}
<form method="post">
  {% csrf_token %}

  <p>Update weights for {{ queryset.count }} selected items:</p>

  {{ form.as_p }}

  <div class="submit-row">
    <input type="hidden" name="action" value="mass_weight_update" />
    <input type="submit" name="apply" value="Apply Changes" class="default" />
    <a href="{{ request.META.HTTP_REFERER }}" class="button cancel-link"
      >Cancel</a
    >
  </div>
</form>
{% endblock %}
```
