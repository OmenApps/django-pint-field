# Usage Guide

- [Usage Guide](#usage-guide)
  - [1. Getting Started](#1-getting-started)
    - [1.1 Installation](#11-installation)
      - [Install the Package](#install-the-package)
      - [Add to INSTALLED\_APPS](#add-to-installed_apps)
      - [Run Migrations](#run-migrations)
      - [Tips for Upgrading from Legacy django-pint-field](#tips-for-upgrading-from-legacy-django-pint-field)
    - [1.2 Basic Configuration](#12-basic-configuration)
      - [Custom Unit Registry Setup](#custom-unit-registry-setup)
      - [Setting Decimal Precision](#setting-decimal-precision)
      - [Available Settings](#available-settings)
      - [Quick Start Example](#quick-start-example)
      - [Verifying Installation](#verifying-installation)
  - [2. Model Fields](#2-model-fields)
    - [2.1 Available Field Types](#21-available-field-types)
      - [IntegerPintField](#integerpintfield)
      - [~~BigIntegerPintField~~ (Deprecated)](#bigintegerpintfield-deprecated)
      - [DecimalPintField](#decimalpintfield)
    - [2.2 Field Parameters](#22-field-parameters)
      - [Required Parameters](#required-parameters)
      - [Optional Parameters](#optional-parameters)
        - [Special DecimalPintField Parameters](#special-decimalpintfield-parameters)
    - [2.3 Basic Model Examples](#23-basic-model-examples)
      - [Simple Model Definition](#simple-model-definition)
      - [Model with Multiple PintFields](#model-with-multiple-pintfields)
      - [Model with Dimensional Validation](#model-with-dimensional-validation)
  - [3. Working with Quantities](#3-working-with-quantities)
    - [3.1 Creating and Saving](#31-creating-and-saving)
      - [Creating Model Instances](#creating-model-instances)
      - [Setting Quantity Values](#setting-quantity-values)
      - [Converting Between Units with Decimal Precision](#converting-between-units-with-decimal-precision)
    - [3.2 Retrieving and Querying](#32-retrieving-and-querying)
      - [Basic Field Access with Decimal Handling](#basic-field-access-with-decimal-handling)
      - [Accessing Magnitude and Units with Decimal Precision](#accessing-magnitude-and-units-with-decimal-precision)
      - [Unit Conversion Methods with Decimal Precision](#unit-conversion-methods-with-decimal-precision)
  - [4. Querying and Filtering](#4-querying-and-filtering)
    - [4.1 Available Lookups](#41-available-lookups)
      - [Exact Match](#exact-match)
      - [Greater Than / Less Than](#greater-than--less-than)
      - [Range](#range)
      - [Null Checks](#null-checks)
    - [4.2 Query Examples](#42-query-examples)
      - [Basic Filtering with Decimal Precision](#basic-filtering-with-decimal-precision)
      - [Range Queries with Decimal Handling](#range-queries-with-decimal-handling)
      - [Complex Queries with Decimal Precision](#complex-queries-with-decimal-precision)
    - [4.3 Limitations and Considerations](#43-limitations-and-considerations)
      - [Unsupported Lookups](#unsupported-lookups)
      - [Unit Compatibility with Decimal Precision](#unit-compatibility-with-decimal-precision)
  - [5. Aggregation Operations](#5-aggregation-operations)
    - [5.1 Available Aggregates](#51-available-aggregates)
      - [PintCount](#pintcount)
      - [PintAvg](#pintavg)
      - [PintSum](#pintsum)
      - [PintMax](#pintmax)
      - [PintMin](#pintmin)
      - [PintStdDev](#pintstddev)
      - [PintVariance](#pintvariance)
  - [6. Forms and Widgets](#6-forms-and-widgets)
    - [6.1 Form Fields](#61-form-fields)
      - [IntegerPintFormField](#integerpintformfield)
      - [DecimalPintFormField](#decimalpintformfield)
    - [6.2 Default Widget (PintFieldWidget)](#62-default-widget-pintfieldwidget)
      - [Basic Usage](#basic-usage)
    - [6.3 Tabled Widget (TabledPintFieldWidget)](#63-tabled-widget-tabledpintfieldwidget)
      - [Features and Benefits](#features-and-benefits)
      - [Configuration Options](#configuration-options)

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

Create instances and query the model:

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

#### ~~BigIntegerPintField~~ (Deprecated)

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
product4 = Product.objects.create(name="Pepper", weight="300.00 gram")
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

```{note}
See the [cheatsheet](./cheatsheet.md) for more examples of unit conversion and quantity manipulation.
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

```{note}
See the [cheatsheet](./cheatsheet.md) for more examples of unit conversion and quantity manipulation.
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
    product.weight, ["kilogram", "pound", "ounce"], precision=2
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
        display_decimal_places=2,
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

## 5. Aggregation Operations

### 5.1 Available Aggregates

django-pint-field provides a comprehensive set of aggregate functions that work seamlessly with PintFields while maintaining unit awareness and proper decimal handling:

#### PintCount

Counts the number of non-null values, returning an Integer.

```python
from django_pint_field.aggregates import PintCount

# Count products with weight specified
weight_count = Product.objects.aggregate(weight_count=PintCount("weight"))
```

#### PintAvg

Calculates the average value, returning a Quantity with proper unit handling.

```python
from django_pint_field.aggregates import PintAvg

# Calculate average weight with decimal precision
avg_weight = Product.objects.aggregate(avg_weight=PintAvg("weight"))
```

#### PintSum

Calculates the sum of values, returning a Quantity with proper decimal handling.

```python
from django_pint_field.aggregates import PintSum

# Calculate total weight with decimal precision
total_weight = Product.objects.aggregate(total_weight=PintSum("weight"))
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

## 6. Forms and Widgets

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
        display_decimal_places=3,  # Display precision
        rounding_method="ROUND_HALF_UP",  # Rounding strategy
        required=True,
        help_text="Enter the precise weight",
        min_value=Decimal("0.001"),  # Minimum allowed value
        max_value=Decimal("1000.000"),  # Maximum allowed value
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
