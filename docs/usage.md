# Usage Guide Outline

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
    ...
    'django_pint_field',
    ...
]
```

#### Run Migrations

```bash
python manage.py migrate django_pint_field
```

```{warning}
Failure to run django-pint-field migrations before running migrations for models using PintFields will result in errors. The migration creates a required composite type in your PostgreSQL database.
```

```{warning}
Previous versions of the package added three compsite types to the database. The newest migration rolls these back and replaces them with a single composite type.
```

### 1.2 Basic Configuration

django-pint-field provides several configuration options that can be set in your project's `settings.py` file.

#### Custom Unit Registry Setup

By default, django-pint-field uses [Pint's](https://pint.readthedocs.io/en/stable/) default unit registry. You can create and configure your own unit registry with custom units:

```python
# settings.py
from pint import UnitRegistry

# Create custom registry
custom_ureg = UnitRegistry()

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

#### Quick Start Example

Here's a complete example showing how to set up a model with a PintField:

```python
# models.py
from django.db import models
from django_pint_field.models import DecimalPintField

class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField(
        'gram',  # default unit
        max_digits=10,
        decimal_places=2,
        unit_choices=['gram', 'kilogram', 'pound'],  # optional
        blank=True,  # optional
        null=True,  # optional
    )

    def __str__(self):
        return f"{self.name} ({self.weight})"
```

```python
# views.py
from django_pint_field.units import ureg
from .models import Product

# Create a product
Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(500, "gram")
)

# Query products
heavy_products = Product.objects.filter(
    weight__gte=ureg.Quantity(1, "kilogram")
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

4. Test a simple model:

```python
from django.core.management import call_command
from django_pint_field.units import ureg

# Create and test a model with a PintField
from myapp.models import Product

# Should work without errors
Product.objects.create(
    name="Test Product",
    weight=ureg.Quantity(100, "gram")
)
```

## 2. Model Fields

Underlying each model field is a composite type in the postgres database, defined in a migration file as:

```sql
CREATE TYPE pint_field AS (comparator decimal, magnitude decimal, units text);
```

- `comparator` is the underlying value, in "[base units](https://pint.readthedocs.io/en/stable/user/systems.html)", which allows us to compare two objects with like units. For instance, to determine if a model instance with a `weight` field value of '300 gram' is greater than another instance with a value of '2 kilogram'. (hint: it is not)
- `magnitude` & `units` together are used to define the Quantity in the user's desired units.

A Pint Quantity created from magnitude and units, then converted to base units, is equal to the comparator.

See Section 8.3 for more details.

### 2.1 Available Field Types

django-pint-field provides three field types to handle different numeric requirements:

#### IntegerPintField

```python
from django_pint_field.models import IntegerPintField

class Product(models.Model):
    weight = IntegerPintField("gram")
```

- Stores magnitude as integer
- Range: -2,147,483,648 to 2,147,483,647
- Best for: Whole number measurements where decimal precision isn't needed

#### BigIntegerPintField

```python
from django_pint_field.models import BigIntegerPintField

class AstronomicalObject(models.Model):
    distance = BigIntegerPintField("lightyear")
```

- Stores magnitude as big integer
- Range: -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807
- Best for: Very large whole numbers
- Note: This field is deprecated as IntegerPintField now provides the same functionality

#### DecimalPintField

```python
from django_pint_field.models import DecimalPintField

class ChemicalSample(models.Model):
    mass = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=4
    )
```

- Stores magnitude as decimal
- Requires `max_digits` and `decimal_places` parameters
- Best for: Precise measurements requiring decimal places

### 2.2 Field Parameters

#### Required Parameters

All PintFields require a default unit:

```python
class Product(models.Model):
    weight = IntegerPintField(
        "gram",  # Required: default unit as string
    )
```

DecimalPintField additionally requires:

```python
class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,    # Required: total number of digits
        decimal_places=2,  # Required: digits after decimal point
    )
```

#### Optional Parameters

```python
class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2,
        unit_choices=['gram', 'kilogram', 'pound'],  # Optional: limit available units
        null=True,                                   # Optional: allow NULL in database
        blank=True,                                  # Optional: allow blank in forms
        help_text="Product weight",                  # Optional: help text for forms
        verbose_name="Weight",                       # Optional: field label
    )
```

##### Special DecimalPintField Parameters

```python
from decimal import ROUND_HALF_UP

class Product(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2,
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
        max_digits=10,
        decimal_places=2
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
        max_digits=8,
        decimal_places=2,
        help_text="Package weight"
    )
    length = DecimalPintField(
        "meter",
        max_digits=6,
        decimal_places=2,
        help_text="Package length"
    )
    width = DecimalPintField(
        "meter",
        max_digits=6,
        decimal_places=2,
        help_text="Package width"
    )
    height = DecimalPintField(
        "meter",
        max_digits=6,
        decimal_places=2,
        help_text="Package height"
    )

    def volume(self):
        """Calculate package volume in cubic meters"""
        return (self.length * self.width * self.height).to("cubic_meter")
```

#### Model with Custom Unit Choices

```python
class Recipe(models.Model):
    name = models.CharField(max_length=100)
    serving_size = DecimalPintField(
        "gram",
        max_digits=8,
        decimal_places=2,
        unit_choices=[
            'gram',
            'kilogram',
            'ounce',
            'pound',
            'serving'  # Assuming custom unit defined in registry
        ]
    )
    cooking_temperature = DecimalPintField(
        "celsius",
        max_digits=5,
        decimal_places=1,
        unit_choices=[
            'celsius',
            'fahrenheit',
            'kelvin'
        ]
    )
    cooking_time = IntegerPintField(
        "minute",
        unit_choices=[
            'second',
            'minute',
            'hour'
        ]
    )
```

#### Model with Dimensional Validation

```python
from django.core.exceptions import ValidationError

class ShippingContainer(models.Model):
    name = models.CharField(max_length=100)
    volume = DecimalPintField(
        "cubic_meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=[
            'cubic_meter',
            'cubic_foot',
            'liter'
        ]
    )

    def clean(self):
        super().clean()
        # Example of custom validation
        if self.volume and self.volume.to('cubic_meter').magnitude < 0:
            raise ValidationError({
                'volume': 'Volume cannot be negative'
            })
        if self.volume and self.volume.to('cubic_meter').magnitude > 100:
            raise ValidationError({
                'volume': 'Volume cannot exceed 100 cubic meters'
            })
```

## 3. Working with Quantities

### 3.1 Creating and Saving

#### Creating Model Instances

There are several ways to create model instances with PintFields:

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

# Method 1: Using Pint Quantity objects
product1 = Product.objects.create(
    name="Flour",
    weight=ureg.Quantity(500, "gram")
)

# Method 2: Using string notation
product2 = Product.objects.create(
    name="Sugar",
    weight=ureg.Quantity("750 gram")
)

# Method 3: Using a tuple of (magnitude, unit)
product3 = Product(
    name="Salt",
    weight=(250, "gram")  # List works too: [250, "gram"]
)
product3.save()
```

#### Setting Quantity Values

You can modify quantity values using various methods:

```python
# Update using Quantity object
product.weight = ureg.Quantity(300, "gram")

# Update using different unit
product.weight = ureg.Quantity(0.3, "kilogram")

# Update using string notation
product.weight = ureg.Quantity("10.5 ounces")

# Update using magnitude and unit separately
product.weight = [400, "gram"]

# Don't forget to save!
product.save()
```

#### Converting Between Units

```python
from django_pint_field.units import ureg

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    ingredient_weight = DecimalPintField(
        'gram',
        max_digits=10,
        decimal_places=2,
        unit_choices=['gram', 'kilogram', 'ounce', 'pound']
    )

    def get_weight_in_preferred_unit(self, unit='gram'):
        """Convert weight to preferred unit"""
        if self.ingredient_weight:
            return self.ingredient_weight.to(unit)
        return None
```

### 3.2 Retrieving and Querying

#### Basic Field Access

```python
# Get the Quantity object
weight = product.weight  # e.g., 500 gram

# Access magnitude (numeric value)
magnitude = product.weight.magnitude  # e.g., 500

# Access units
units = product.weight.units  # e.g., gram

# String representation
weight_str = str(product.weight)  # e.g., "500 gram"
```

#### Accessing Magnitude and Units

```python
class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    def get_weight_components(self):
        """Return magnitude and units separately"""
        return {
            'magnitude': self.weight.magnitude,
            'units': str(self.weight.units),
            'base_magnitude': self.weight.to_base_units().magnitude
        }

    def is_heavy(self):
        """Example of comparing quantities"""
        return self.weight.to('kilogram').magnitude > 1

    @property
    def weight_formatted(self):
        """Format weight with custom precision"""
        if self.weight:
            return f"{self.weight.magnitude:.1f} {self.weight.units}"
        return "No weight specified"
```

#### Unit Conversion Methods

```python
# Direct conversion
kilos = product.weight.to('kilogram')

# Multiple conversions
conversions = {
    'kg': product.weight.to('kilogram'),
    'lb': product.weight.to('pound'),
    'oz': product.weight.to('ounce')
}

# Conversion with formatting
def format_weight(quantity, unit, precision=2):
    """Convert and format a weight quantity"""
    converted = quantity.to(unit)
    return f"{converted.magnitude:.{precision}f} {converted.units}"

# Usage:
formatted = format_weight(product.weight, 'kilogram', 3)
```

### 3.3 Field Properties

#### Available Unit Conversions

Fields automatically provide conversion properties for compatible units:

```python
class WeightMeasurement(models.Model):
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    def get_all_conversions(self):
        """Get all common mass unit conversions"""
        if not self.weight:
            return {}

        return {
            'gram': self.weight.to('gram'),
            'kilogram': self.weight.to('kilogram'),
            'milligram': self.weight.to('milligram'),
            'pound': self.weight.to('pound'),
            'ounce': self.weight.to('ounce')
        }

# Access built-in conversion properties
measurement = WeightMeasurement.objects.first()
kg_value = measurement.weight__kilogram  # Double underscore property
gram_value = measurement.weight__gram
```

#### Validation Behavior

PintFields include built-in validation:

```python
class Product(models.Model):
    weight = DecimalPintField(
        'gram',
        max_digits=6,
        decimal_places=2,
        unit_choices=['gram', 'kilogram']
    )

    def clean(self):
        super().clean()
        if self.weight:
            # Dimensionality validation (automatic)
            # Would raise ValidationError if assigning a length unit
            #   instead of a weight, for instance

            # Custom range validation
            min_weight = 0.1 * ureg.kilogram
            max_weight = 100 * ureg.kilogram

            if self.weight < min_weight:
                raise ValidationError({
                    'weight': f'Weight must be at least {min_weight}'
                })
            if self.weight > max_weight:
                raise ValidationError({
                    'weight': f'Weight cannot exceed {max_weight}'
                })

            # Precision validation (automatic for DecimalPintField)
            # Will raise ValidationError if exceeds max_digits or decimal_places
```

## 4. Querying and Filtering

### 4.1 Available Lookups

django-pint-field supports the following lookup types:

#### Exact Match

```python
# Find products weighing exactly 500 grams
Product.objects.filter(weight__exact=ureg.Quantity('500 gram'))

# Shorthand syntax
Product.objects.filter(weight=ureg.Quantity('500 gram'))
```

#### Greater Than / Less Than

```python
# Greater than (gt)
Product.objects.filter(weight__gt=ureg.Quantity('1 kilogram'))

# Greater than or equal to (gte)
Product.objects.filter(weight__gte=ureg.Quantity('1 kilogram'))

# Less than (lt)
Product.objects.filter(weight__lt=ureg.Quantity('500 gram'))

# Less than or equal to (lte)
Product.objects.filter(weight__lte=ureg.Quantity('500 gram'))
```

#### Range

```python
# Find products within a weight range
min_weight = ureg.Quantity('100 gram')
max_weight = ureg.Quantity('1 kilogram')
Product.objects.filter(weight__range=(min_weight, max_weight))
```

#### Null Checks

```python
# Find products with no weight specified
Product.objects.filter(weight__isnull=True)

# Find products with weight specified
Product.objects.filter(weight__isnull=False)
```

### 4.2 Query Examples

#### Basic Filtering

```python
from django_pint_field.units import ureg
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

# Simple equality
light_products = Product.objects.filter(
    weight=ureg.Quantity('100 gram')
)

# Comparison with different units (automatically converted)
heavy_products = Product.objects.filter(
    weight__gte=ureg.Quantity('1 kilogram')
)

# Multiple conditions
medium_products = Product.objects.filter(
    weight__gt=ureg.Quantity('250 gram'),
    weight__lt=ureg.Quantity('750 gram')
)

# Combining with OR conditions
from django.db.models import Q

mixed_products = Product.objects.filter(
    Q(weight__lt=ureg.Quantity('100 gram')) |
    Q(weight__gt=ureg.Quantity('1 kilogram'))
)
```

#### Range Queries

```python
class ShippingRate(models.Model):
    min_weight = DecimalPintField('gram', max_digits=10, decimal_places=2)
    max_weight = DecimalPintField('gram', max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

# Find applicable shipping rate for a package
def get_shipping_rate(package_weight):
    return ShippingRate.objects.filter(
        min_weight__lte=package_weight,
        max_weight__gt=package_weight
    ).first()

# Find overlapping weight ranges
def find_overlapping_rates():
    return ShippingRate.objects.filter(
        min_weight__lt=models.F('max_weight')
    ).exclude(
        max_weight__lte=models.F('min_weight')
    )
```

#### Complex Queries

```python
from django.db.models import F, ExpressionWrapper, DecimalField

class Shipment(models.Model):
    actual_weight = DecimalPintField('kilogram', max_digits=10, decimal_places=2)
    volume = DecimalPintField('cubic_meter', max_digits=10, decimal_places=3)

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
            actual_weight__gt=F('volume') * ureg.gram
        )

    @classmethod
    def get_shipments_by_weight_category(cls):
        """Categorize shipments by weight ranges"""
        categories = {
            'light': (0, 10),  # kg
            'medium': (10, 50),
            'heavy': (50, 100),
            'extra_heavy': (100, None)
        }

        queries = []
        for category, (min_weight, max_weight) in categories.items():
            q = Q()
            if min_weight is not None:
                q &= Q(actual_weight__gte=ureg.Quantity(f'{min_weight} kilogram'))
            if max_weight is not None:
                q &= Q(actual_weight__lt=ureg.Quantity(f'{max_weight} kilogram'))
            queries.append((category, q))

        return {
            category: cls.objects.filter(query).count()
            for category, query in queries
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

#### Performance Considerations

```python
class InventoryItem(models.Model):
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['weight']),  # Indexes the composite field
        ]

    @classmethod
    def bulk_convert_weights(cls, unit='kilogram'):
        """Efficient bulk conversion of weights"""
        items = cls.objects.all()
        # Use iterator() for large querysets to reduce memory usage
        for item in items.iterator():
            converted_weight = item.weight.to(unit)
            print(f"Original: {item.weight}, Converted: {converted_weight}")
```

#### Unit Compatibility

```python
from django.core.exceptions import ValidationError

class Product(models.Model):
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)
    size = DecimalPintField('meter', max_digits=10, decimal_places=2)

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
        """Safely compare two weight quantities"""
        try:
            # Use the comparator, which is always in base units
            # Will not raise an exception:
            return base_weight1.comparator < base_weight2.comparator
        except:
            raise ValidationError("Incompatible units for comparison")
```

#### Best Practices for Querying

```python
class Product(models.Model):
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    @classmethod
    def get_by_weight_range(cls, min_weight, max_weight, unit='gram'):
        """
        Safely query by weight range with unit conversion

        Args:
            min_weight: Numeric minimum weight
            max_weight: Numeric maximum weight
            unit: Unit string (default: 'gram')
        """
        try:
            min_q = ureg.Quantity(min_weight, unit)
            max_q = ureg.Quantity(max_weight, unit)

            return cls.objects.filter(
                weight__gte=min_q,
                weight__lte=max_q
            )
        except Exception as e:
            raise ValidationError(f"Invalid weight range: {str(e)}")

    @classmethod
    def get_weight_distribution(cls, ranges, unit='kilogram'):
        """
        Get count of products in each weight range

        Args:
            ranges: List of (min, max) tuples in specified unit
            unit: Unit string for the ranges
        """
        distribution = {}
        for min_val, max_val in ranges:
            count = cls.get_by_weight_range(
                min_val, max_val, unit
            ).count()
            distribution[f"{min_val}-{max_val} {unit}"] = count
        return distribution
```

## 5. Aggregation Operations

### 5.1 Available Aggregates

django-pint-field provides several aggregate functions that work with PintFields while maintaining unit awareness:

#### PintAvg

Calculates the average value, returning a Quantity.

```python
from django_pint_field.aggregates import PintAvg

# Calculate average weight
avg_weight = Product.objects.aggregate(
    avg_weight=PintAvg('weight')
)
```

#### PintCount

Counts the number of non-null values, returning an Integer.

```python
from django_pint_field.aggregates import PintCount

# Count products with weight specified
weight_count = Product.objects.aggregate(
    weight_count=PintCount('weight')
)
```

#### PintMax

Returns the maximum value, returning a Quantity.

```python
from django_pint_field.aggregates import PintMax

# Find heaviest product weight
max_weight = Product.objects.aggregate(
    max_weight=PintMax('weight')
)
```

#### PintMin

Returns the minimum value, returning a Quantity.

```python
from django_pint_field.aggregates import PintMin

# Find lightest product weight
min_weight = Product.objects.aggregate(
    min_weight=PintMin('weight')
)
```

#### PintStdDev

Calculates the standard deviation, returning a Quantity.

```python
from django_pint_field.aggregates import PintStdDev

# Calculate weight standard deviation
std_dev = Product.objects.aggregate(
    std_dev=PintStdDev('weight')
)

# With sample parameter
sample_std_dev = Product.objects.aggregate(
    std_dev=PintStdDev('weight', sample=True)
)
```

#### PintSum

Calculates the sum of values, returning a Quantity.

```python
from django_pint_field.aggregates import PintSum

# Calculate total weight
total_weight = Product.objects.aggregate(
    total_weight=PintSum('weight')
)
```

#### PintVariance

Calculates the variance, returning a Quantity.

```python
from django_pint_field.aggregates import PintVariance

# Calculate weight variance
variance = Product.objects.aggregate(
    variance=PintVariance('weight')
)

# With sample parameter
sample_variance = Product.objects.aggregate(
    variance=PintVariance('weight', sample=True)
)
```

### 5.2 Usage Examples

#### Simple Aggregations

```python
from django_pint_field.aggregates import (
    PintAvg, PintCount, PintMax, PintMin, PintSum
)
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

class Product(models.Model):
    name = models.CharField(max_length=100)
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    @classmethod
    def get_weight_statistics(cls):
        """Get comprehensive weight statistics"""
        stats = cls.objects.aggregate(
            total_weight=PintSum('weight'),
            average_weight=PintAvg('weight'),
            min_weight=PintMin('weight'),
            max_weight=PintMax('weight'),
            product_count=PintCount('weight')
        )

        return {
            'total': stats['total_weight'].to('kilogram'),
            'average': stats['average_weight'].to('gram'),
            'min': stats['min_weight'].to('gram'),
            'max': stats['max_weight'].to('kilogram'),
            'count': stats['product_count']
        }
```

#### Combining Aggregates

```python
class Shipment(models.Model):
    weight = DecimalPintField('kilogram', max_digits=10, decimal_places=2)
    volume = DecimalPintField('cubic_meter', max_digits=10, decimal_places=3)

    @classmethod
    def get_shipping_metrics(cls):
        """Calculate multiple metrics together"""
        metrics = cls.objects.aggregate(
            total_weight=PintSum('weight'),
            avg_weight=PintAvg('weight'),
            total_volume=PintSum('volume'),
            avg_volume=PintAvg('volume'),
            shipment_count=PintCount('id')
        )

        # Calculate density if there are shipments
        if metrics['shipment_count'] > 0:
            avg_density = (
                metrics['total_weight'].to('kilogram').magnitude /
                metrics['total_volume'].to('cubic_meter').magnitude
            )
        else:
            avg_density = 0

        return {
            **metrics,
            'average_density': f"{avg_density:.2f} kg/m³"
        }
```

#### Unit Handling in Aggregates

```python
class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    def get_total_weight(self):
        """Calculate total weight for this inventory item"""
        return self.quantity * self.unit_weight

    @classmethod
    def get_inventory_analysis(cls, output_unit='kilogram'):
        """
        Analyze inventory with custom output units

        Args:
            output_unit: Desired unit for weight outputs
        """
        base_stats = cls.objects.aggregate(
            total_items=models.Sum('quantity'),
            total_weight=PintSum(
                models.F('quantity') * models.F('unit_weight')
            ),
            avg_unit_weight=PintAvg('unit_weight'),
            heaviest_unit=PintMax('unit_weight'),
            lightest_unit=PintMin('unit_weight')
        )

        # Convert all weight measurements to desired unit
        converted_stats = {
            'total_items': base_stats['total_items'],
            'total_weight': base_stats['total_weight'].to(output_unit),
            'avg_unit_weight': base_stats['avg_unit_weight'].to(output_unit),
            'heaviest_unit': base_stats['heaviest_unit'].to(output_unit),
            'lightest_unit': base_stats['lightest_unit'].to(output_unit)
        }

        return converted_stats

    @classmethod
    def get_weight_distribution(cls, bins=5):
        """
        Calculate weight distribution across inventory

        Args:
            bins: Number of weight ranges to create
        """
        weights = cls.objects.aggregate(
            min_weight=PintMin('unit_weight'),
            max_weight=PintMax('unit_weight')
        )

        min_weight = weights['min_weight'].to('gram').magnitude
        max_weight = weights['max_weight'].to('gram').magnitude
        bin_size = (max_weight - min_weight) / bins

        distribution = {}
        for i in range(bins):
            bin_min = min_weight + (i * bin_size)
            bin_max = bin_min + bin_size
            count = cls.objects.filter(
                unit_weight__gte=ureg.Quantity(f"{bin_min} gram"),
                unit_weight__lt=ureg.Quantity(f"{bin_max} gram")
            ).count()

            distribution[f"{bin_min:.0f}g - {bin_max:.0f}g"] = count

        return distribution
```

#### Best Practices for Aggregations

```python
class WeightMeasurement(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = DecimalPintField('gram', max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['weight']),  # Indexes the composite field
        ]

    @classmethod
    def analyze_measurements(cls, start_date=None, end_date=None):
        """
        Analyze weight measurements with proper error handling
        and unit conversion
        """
        queryset = cls.objects.all()

        # Apply date filtering if provided
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        try:
            stats = queryset.aggregate(
                count=PintCount('weight'),
                total=PintSum('weight'),
                average=PintAvg('weight'),
                std_dev=PintStdDev('weight'),
                variance=PintVariance('weight')
            )

            # Convert to appropriate units based on magnitude
            if stats['average']:
                avg_magnitude = stats['average'].to('gram').magnitude

                if avg_magnitude > 1000:
                    unit = 'kilogram'
                else:
                    unit = 'gram'

                stats = {
                    'count': stats['count'],
                    'total': stats['total'].to(unit),
                    'average': stats['average'].to(unit),
                    'std_dev': stats['std_dev'].to(unit),
                    'variance': stats['variance'].to(unit * unit),
                    'unit': unit
                }

            return stats

        except Exception as e:
            logger.error(f"Error analyzing measurements: {str(e)}")
            return None
```

## 6. Forms, Widgets, and Admin

### 6.1 Form Fields

django-pint-field provides two form field types that correspond to the model fields:

#### IntegerPintFormField

Used with IntegerPintField and BigIntegerPintField models:

```python
from django import forms
from django_pint_field.forms import IntegerPintFormField

class ProductForm(forms.Form):
    weight = IntegerPintFormField(
        default_unit='gram',
        unit_choices=['gram', 'kilogram', 'pound'],
        required=True,
        help_text="Enter the product weight"
    )
```

#### DecimalPintFormField

Used with DecimalPintField models:

```python
from django_pint_field.forms import DecimalPintFormField

class PreciseProductForm(forms.Form):
    weight = DecimalPintFormField(
        default_unit='gram',
        unit_choices=['gram', 'kilogram', 'pound'],
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text="Enter the precise weight"
    )
```

#### Field Parameters and Options

Both form fields accept these common parameters:

```python
class WeightForm(forms.ModelForm):
    weight = DecimalPintFormField(
        default_unit='gram',              # Required: Base unit for the field
        unit_choices=['gram', 'kilogram', 'pound'],  # Optional: Available units
        required=True,                    # Optional: Whether field is required
        label='Weight',                   # Optional: Field label
        help_text='Product weight',       # Optional: Help text
        disabled=False,                   # Optional: Disable field
        initial=None,                     # Optional: Initial value
        widget=None,                      # Optional: Custom widget
    )

    class Meta:
        model = Product
        fields = ['weight']
```

DecimalPintFormField specific parameters:

```python
class PreciseWeightForm(forms.ModelForm):
    weight = DecimalPintFormField(
        default_unit='gram',
        max_digits=10,                    # Required for DecimalPintFormField
        decimal_places=2,                 # Required for DecimalPintFormField
        display_decimal_places=2,         # Optional: Displayed decimal places
    )
```

### 6.2 Default Widget (PintFieldWidget)

The PintFieldWidget is the default widget for PintFields. It combines a numeric input with a unit selection dropdown.

#### Basic Usage

```python
from django_pint_field.widgets import PintFieldWidget

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['weight']
        widgets = {
            'weight': PintFieldWidget(
                default_unit='gram',
                unit_choices=['gram', 'kilogram', 'pound']
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
        self.widgets[0].attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter value',
            'min': '0',
            'step': '0.01'
        })

        # Customize the unit select
        self.widgets[1].attrs.update({
            'class': 'form-select',
        })

class CustomProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['weight']
        widgets = {
            'weight': CustomPintWidget(
                default_unit='gram',
                unit_choices=['gram', 'kilogram', 'pound'],
                attrs={
                    'class': 'weight-input-group'
                }
            )
        }
```

#### Example Implementation

```python
from django import forms
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.units import ureg

class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure widget
        self.fields['weight'].widget = PintFieldWidget(
            default_unit='gram',
            unit_choices=['gram', 'kilogram', 'pound'],
            attrs={
                'class': 'weight-input',
                'data-toggle': 'tooltip',
                'title': 'Enter product weight'
            }
        )

    def clean_weight(self):
        """Custom validation for weight field"""
        weight = self.cleaned_data.get('weight')
        if weight:
            min_weight = ureg.Quantity('10 gram')
            max_weight = ureg.Quantity('1000 kilogram')

            if weight < min_weight:
                raise forms.ValidationError(
                    f'Weight must be at least {min_weight}'
                )
            if weight > max_weight:
                raise forms.ValidationError(
                    f'Weight cannot exceed {max_weight}'
                )
        return weight

    class Meta:
        model = Product
        fields = ['name', 'weight']
```

### 6.3 Tabled Widget (TabledPintFieldWidget)

The TabledPintFieldWidget extends the basic PintFieldWidget by adding a table showing the value converted to all available units.

![TabledPintFieldWidget](https://raw.githubusercontent.com/jacklinke/django-pint-field/main/media/TabledPintFieldWidget.png)

#### Features and Benefits

- Shows value in all available units simultaneously
- Updates conversions in real-time
- Helps users understand unit relationships
- Reduces conversion errors

#### Configuration Options

```python
from django_pint_field.widgets import TabledPintFieldWidget

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['weight']
        widgets = {
            'weight': TabledPintFieldWidget(
                default_unit='gram',
                unit_choices=['gram', 'kilogram', 'pound'],
                floatformat=2,                    # Number of decimal places in table
                table_class='conversion-table',   # CSS class for table
                td_class='text-end',             # CSS class for table cells
            )
        }
```

#### Template Customization

The widget template can be overridden by creating a template at:
`templates/django_pint_field/tabled_django_pint_field_widget.html`

Example custom template:

```html
{% spaceless %}{% for widget in widget.subwidgets %}{% include
widget.template_name %}{% endfor %}{% endspaceless %} {% if values_list %}
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
      <td style="text-align: right" class="{{ td_class }}">
        {{ value_item.magnitude|floatformat:floatformat }}
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
<br />
{% endif %}
```

#### Example Implementation

```python
class WeightForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get field's default unit and choices
        weight_field = self.fields['weight']
        default_unit = weight_field.default_unit
        unit_choices = weight_field.unit_choices

        # Configure tabled widget
        self.fields['weight'].widget = TabledPintFieldWidget(
            default_unit=default_unit,
            unit_choices=unit_choices,
            floatformat=2,
            table_class='table table-striped table-hover',
            td_class='text-end'
        )

    class Meta:
        model = Product
        fields = ['name', 'weight']

    class Media:
        css = {
            'all': ['css/weight-form.css']
        }
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
```

### 6.4 Django Admin Integration

#### 6.4.1 Basic ModelAdmin Setup

The django-pint-field package provides seamless integration with Django's admin interface. Here's how to set up and customize your admin for models with PintFields:

##### Registering Models with PintFields

(Same as any other model)

```python
from django.contrib import admin
from django_pint_field.units import ureg
from .models import WeightModel

@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight']
    search_fields = ['name']
    ordering = ['name']
```

##### Default Admin Representation

PintFields are automatically rendered in the admin with their default units. However, you can customize their display:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['weight_base_value']
        return []

    def weight_base_value(self, obj):
        """Display the base unit value"""
        if obj.weight:
            return obj.weight.to_base_units()
    weight_base_value.short_description = 'Base Weight Value'
```

##### List Display Configuration

You can display weights in multiple units using custom methods:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'weight',
        'get_weight_kg',
        'get_weight_lb',
        'get_weight_oz'
    ]

    def get_weight_kg(self, obj):
        """Display weight in kilograms"""
        if obj.weight:
            kg = obj.weight.to('kilogram')
            return f"{kg.magnitude:.2f} {kg.units}"
    get_weight_kg.short_description = 'Weight (kg)'

    def get_weight_lb(self, obj):
        """Display weight in pounds"""
        if obj.weight:
            lb = obj.weight.to('pound')
            return f"{lb.magnitude:.2f} {lb.units}"
    get_weight_lb.short_description = 'Weight (lb)'

    def get_weight_oz(self, obj):
        """Display weight in ounces"""
        if obj.weight:
            oz = obj.weight.to('ounce')
            return f"{oz.magnitude:.1f} {oz.units}"
    get_weight_oz.short_description = 'Weight (oz)'
```

##### Using Property Shortcuts

django-pint-field provides a convenient shortcut for unit conversion using double underscores:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'weight',  # Original value
        'weight__kilogram',  # Converted to kg
        'weight__pound',     # Converted to lb
        'weight__ounce'      # Converted to oz
    ]

    list_display_links = ['name', 'weight']
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
        'name',
        'formatted_weight',
        'weight_status',
        'weight__kilogram',
    ]

    def formatted_weight(self, obj):
        """Custom formatted weight display"""
        if not obj.weight:
            return '-'

        # Format based on magnitude
        magnitude = obj.weight.to('gram').magnitude
        if magnitude >= 1000:
            value = obj.weight.to('kilogram')
            color = 'red'
        else:
            value = obj.weight
            color = 'green'

        return format_html(
            '<span style="color: {};">{:.2f} {}</span>',
            color,
            value.magnitude,
            value.units
        )
    formatted_weight.short_description = 'Weight'
    formatted_weight.admin_order_field = 'weight'

    def weight_status(self, obj):
        """Display weight status with icon"""
        if not obj.weight:
            return '-'

        threshold = ureg.Quantity('500 gram')
        if obj.weight > threshold:
            icon = '⬆️'
            text = 'Heavy'
        else:
            icon = '⬇️'
            text = 'Light'

        return format_html('{} {}', icon, text)
    weight_status.short_description = 'Status'
```

### 6.4.2 Custom Admin Forms

#### Custom Admin Forms Implementation

##### Overriding Default Widgets

```python
from django import forms
from django.contrib import admin
from django_pint_field.widgets import TabledPintFieldWidget
from .models import WeightModel

class WeightModelAdminForm(forms.ModelForm):
    class Meta:
        model = WeightModel
        fields = '__all__'
        widgets = {
            'weight': TabledPintFieldWidget(
                default_unit='gram',
                unit_choices=['gram', 'kilogram', 'pound'],
                floatformat=2,
                table_class='admin-weight-table'
            )
        }

class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
```

##### Manually Adding Unit Conversion Displays

```python
from django.utils.html import format_html

class WeightModelAdminForm(forms.ModelForm):
    converted_weights = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = WeightModel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        if instance and instance.weight:
            self.fields['converted_weights'].initial = self.get_conversions(instance.weight)

    def get_conversions(self, weight):
        conversions = {
            'gram': weight.to('gram'),
            'kilogram': weight.to('kilogram'),
            'pound': weight.to('pound'),
            'ounce': weight.to('ounce')
        }
        return format_html(
            '<div class="weight-conversions">'
            '<table class="conversion-table">'
            '<tr><th>Unit</th><th>Value</th></tr>'
            '{}'
            '</table></div>',
            format_html_join(
                '\n',
                '<tr><td>{}</td><td>{:.3f}</td></tr>',
                ((unit, value.magnitude) for unit, value in conversions.items())
            )
        )

class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
    readonly_fields = ['converted_weights']
```

##### Form Field Customization

```python
class WeightModelAdminForm(forms.ModelForm):
    min_weight = forms.DecimalField(required=False, disabled=True)
    max_weight = forms.DecimalField(required=False, disabled=True)

    class Meta:
        model = WeightModel
        fields = '__all__'
        widgets = {
            'weight': TabledPintFieldWidget(
                default_unit='gram',
                unit_choices=['gram', 'kilogram', 'pound'],
                floatformat=2
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize weight field
        self.fields['weight'].help_text = 'Enter weight in any supported unit'
        self.fields['weight'].widget.attrs.update({
            'class': 'weight-input',
            'data-validation': 'weight'
        })

        # Set min/max values if instance exists
        if self.instance.pk:
            category = self.instance.category
            if category:
                self.fields['min_weight'].initial = category.min_weight
                self.fields['max_weight'].initial = category.max_weight

class WeightModelAdmin(admin.ModelAdmin):
    form = WeightModelAdminForm
    fieldsets = (
        (None, {
            'fields': ('name', 'category')
        }),
        ('Weight Information', {
            'fields': ('weight', 'converted_weights'),
            'classes': ('weight-fieldset',),
            'description': 'Enter and view weight in various units'
        }),
        ('Weight Limits', {
            'fields': ('min_weight', 'max_weight'),
            'classes': ('collapse',)
        })
    )
```

### 6.4.3 List Display and Filtering

#### Custom List Filters

```python
from django.contrib import admin
from django_pint_field.units import ureg

class WeightRangeFilter(admin.SimpleListFilter):
    title = 'weight range'
    parameter_name = 'weight_range'

    def lookups(self, request, model_admin):
        return (
            ('light', 'Light (< 100g)'),
            ('medium', 'Medium (100g - 1kg)'),
            ('heavy', 'Heavy (> 1kg)'),
            ('very_heavy', 'Very Heavy (> 10kg)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'light':
            return queryset.filter(
                weight__lt=ureg.Quantity('100 gram')
            )
        elif self.value() == 'medium':
            return queryset.filter(
                weight__gte=ureg.Quantity('100 gram'),
                weight__lt=ureg.Quantity('1 kilogram')
            )
        elif self.value() == 'heavy':
            return queryset.filter(
                weight__gte=ureg.Quantity('1 kilogram'),
                weight__lt=ureg.Quantity('10 kilogram')
            )
        elif self.value() == 'very_heavy':
            return queryset.filter(
                weight__gte=ureg.Quantity('10 kilogram')
            )
```

#### Unit Conversion in List Display

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight_with_conversions', 'category']
    list_filter = [WeightRangeFilter, 'category']  # Defined above

    def weight_with_conversions(self, obj):
        if not obj.weight:
            return '-'

        # Convert to common units
        in_g = obj.weight.to('gram')
        in_kg = obj.weight.to('kilogram')
        in_lb = obj.weight.to('pound')

        return format_html(
            '<div class="weight-display">'
            '<span class="primary-weight">{:.2f} {}</span>'
            '<div class="weight-conversions">'
            '<small>({:.2f} {}, {:.2f} {})</small>'
            '</div>'
            '</div>',
            obj.weight.magnitude, obj.weight.units,
            in_kg.magnitude, in_kg.units,
            in_lb.magnitude, in_lb.units
        )
    weight_with_conversions.short_description = 'Weight'
    weight_with_conversions.admin_order_field = 'weight'

    class Media:
        css = {
            'all': ['admin/css/weight_display.css']
        }
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

#### Search Functionality

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'category']
    list_filter = [WeightRangeFilter, 'category']  # Defined above
    search_fields = ['name', 'category__name']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Try to parse search term as a weight
        try:
            search_quantity = ureg.Quantity(search_term)
            # Add weight-based filtering
            weight_q = Q(weight__gte=search_quantity.to('gram') * 0.9) & \
                      Q(weight__lte=search_quantity.to('gram') * 1.1)
            queryset |= self.model.objects.filter(weight_q)
        except:
            pass

        return queryset, use_distinct
```

### 6.4.4 Admin Actions

#### Bulk Unit Conversion Actions

Remember that the underlying `comparator` on all model fields is in base units, but we can modify the magnitude and units for a set of model instances - without affecting the comparator - using this example.

```python
from django.contrib import admin
from django.contrib import messages
from django_pint_field.units import ureg

@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    actions = [
        'convert_to_kilograms',
        'convert_to_pounds',
        'standardize_units',
    ]

    @admin.action(description='Convert selected weights to kilograms')
    def convert_to_kilograms(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.weight:
                obj.weight = obj.weight.to('kilogram')
                obj.save()
                updated += 1

        self.message_user(
            request,
            f'Successfully converted {updated} weights to kilograms.',
            messages.SUCCESS
        )

    @admin.action(description='Convert selected weights to pounds')
    def convert_to_pounds(self, request, queryset):
        updated = 0
        errors = 0

        for obj in queryset:
            try:
                if obj.weight:
                    obj.weight = obj.weight.to('pound')
                    obj.save()
                    updated += 1
            except Exception as e:
                errors += 1

        if updated:
            self.message_user(
                request,
                f'Successfully converted {updated} weights to pounds.',
                messages.SUCCESS
            )
        if errors:
            self.message_user(
                request,
                f'Failed to convert {errors} weights.',
                messages.ERROR
            )

    @admin.action(description='Standardize units based on magnitude')
    def standardize_units(self, request, queryset):
        """Convert weights to the most appropriate unit based on magnitude"""
        updated = 0

        for obj in queryset:
            if not obj.weight:
                continue

            # Convert to grams to check magnitude
            weight_in_g = obj.weight.to('gram')
            magnitude = weight_in_g.magnitude

            # Choose appropriate unit
            if magnitude >= 1_000_000:  # 1,000 kg
                new_unit = 'metric_ton'
            elif magnitude >= 1_000:    # 1 kg
                new_unit = 'kilogram'
            elif magnitude >= 1:        # 1 g
                new_unit = 'gram'
            else:
                new_unit = 'milligram'

            obj.weight = obj.weight.to(new_unit)
            obj.save()
            updated += 1

        self.message_user(
            request,
            f'Successfully standardized units for {updated} weights.',
            messages.SUCCESS
        )
```

#### Export with Specific Units

```python
import csv
from django.http import HttpResponse

class WeightModelAdmin(admin.ModelAdmin):
    actions = ['export_as_csv']

    @admin.action(description='Export selected items to CSV')
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        # Write header with unit specifications
        header = field_names + ['weight_kg', 'weight_lb', 'weight_g']
        writer.writerow(header)

        # Write data rows
        for obj in queryset:
            row_data = [getattr(obj, field) for field in field_names]

            # Add weight in different units
            if obj.weight:
                row_data.extend([
                    obj.weight.to('kilogram').magnitude,
                    obj.weight.to('pound').magnitude,
                    obj.weight.to('gram').magnitude,
                ])
            else:
                row_data.extend(['', '', ''])

            writer.writerow(row_data)

        return response
```

#### Mass Update Actions

```python
from django import forms
from django.contrib.admin import helpers
from django.template.response import TemplateResponse

class MassWeightUpdateForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    conversion_unit = forms.ChoiceField(
        choices=[
            ('gram', 'Grams'),
            ('kilogram', 'Kilograms'),
            ('pound', 'Pounds'),
        ],
        required=True
    )
    adjustment_factor = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=1.0,
        help_text='Multiply current weights by this factor'
    )

class WeightModelAdmin(admin.ModelAdmin):
    actions = ['mass_weight_update']

    @admin.action(description='Mass update weights')
    def mass_weight_update(self, request, queryset):
        form = None

        if 'apply' in request.POST:
            form = MassWeightUpdateForm(request.POST)

            if form.is_valid():
                conversion_unit = form.cleaned_data['conversion_unit']
                adjustment_factor = form.cleaned_data['adjustment_factor']

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
                        f'Successfully updated {updated} weights.',
                        messages.SUCCESS
                    )
                if errors:
                    self.message_user(
                        request,
                        f'Failed to update {errors} weights.',
                        messages.ERROR
                    )
                return None

        if not form:
            form = MassWeightUpdateForm(initial={
                '_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
            })

        context = {
            'title': 'Mass Update Weights',
            'form': form,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'queryset': queryset,
            'opts': self.model._meta,
        }

        return TemplateResponse(
            request,
            'admin/mass_weight_update.html',
            context
        )
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

## 7. REST Framework Integration

Django Pint Field provides seamless integration with Django REST Framework (DRF) through specialized serializer fields. This integration allows you to serialize and deserialize Pint quantities in your API endpoints while maintaining unit consistency and proper validation.

### 7.1 Serializer Fields

Django Pint Field provides two main serializer fields for use with DRF:

- **IntegerPintRestField**: For use with `IntegerPintField` and `BigIntegerPintField`
- **DecimalPintRestField**: For use with `DecimalPintField`

Both fields support either string-based or dictionary-based serialization formats.

#### String Format

The string format provides a more compact, human-readable representation:

- IntegerPintRestField: `"1 gram"` or `"Quantity(1 gram)"`
- DecimalPintRestField: `"1.5 gram"` or `"Quantity(1.5 gram)"`

#### Dictionary Format

The dictionary format provides a more structured representation:

```python
{
    "magnitude": 1.5,
    "units": "gram"
}
```

### 7.2 Serializer Examples

#### Basic Serializer Setup

Assuming a `WeightModel` with `weight` as an IntegerPintField and `precise_weight` as a DecimalPintField.

```python
from rest_framework import serializers
from django_pint_field.rest import IntegerPintRestField, DecimalPintRestField

class WeightSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()
    precise_weight = DecimalPintRestField()

    class Meta:
        model = WeightModel
        fields = ['id', 'name', 'weight', 'precise_weight']
```

#### Using the Wrapped Representation

The default output is a string with the magnitude and units. But we can set `wrap=True` in the serializer to wrap with `Quantity()`

```python
from rest_framework import serializers
from django_pint_field.rest import IntegerPintRestField, DecimalPintRestField

class WeightSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField(wrap=True)
    precise_weight = DecimalPintRestField(wrap=True)

    class Meta:
        model = WeightModel
        fields = ['id', 'name', 'weight', 'precise_weight']

# Example output:
# {
#     "id": 1,
#     "name": "Sample Weight",
#     "weight": "Quantity(1000 gram)"
#     "precise_weight": "Quantity(1000.372 gram)"
# }
```

#### Using Dictionary Format with PintRestField

```python
from rest_framework import serializers
from django_pint_field.rest import PintRestField

class WeightSerializer(serializers.ModelSerializer):
    weight = PintRestField()

    class Meta:
        model = WeightModel
        fields = ['id', 'name', 'weight']

# Example output:
# {
#     "id": 1,
#     "name": "Sample Weight",
#     "weight": {
#         "magnitude": 1000,
#         "units": "gram"
#     }
# }
```

#### Custom Field Handling

You can customize how the fields handle units and validation:

```python
from rest_framework import serializers
from django_pint_field.rest import DecimalPintRestField
from django_pint_field.units import ureg

class WeightSerializer(serializers.ModelSerializer):
    # Custom field with validation
    weight = DecimalPintRestField()

    class Meta:
        model = WeightModel
        fields = ['id', 'name', 'weight']

    def validate_weight(self, value):
        # Convert to kilograms for validation
        kg_value = value.to(ureg.kilogram)
        if kg_value.magnitude > 1000:
            raise serializers.ValidationError("Weight cannot exceed 1000 kg")
        return value
```

#### Unit Conversion in Serializers

You can perform unit conversions during serialization:

```python
from rest_framework import serializers
from django_pint_field.rest import DecimalPintRestField
from django_pint_field.units import ureg

class WeightSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField(wrap=True)
    weight_in_kg = serializers.SerializerMethodField()
    weight_in_lbs = serializers.SerializerMethodField()

    class Meta:
        model = WeightModel
        fields = ['id', 'name', 'weight', 'weight_in_kg', 'weight_in_lbs']

    def get_weight_in_kg(self, obj):
        if obj.weight:
            converted = obj.weight.to(ureg.kilogram)
            return f"{converted.magnitude:.2f} kg"
        return None

    def get_weight_in_lbs(self, obj):
        if obj.weight:
            converted = obj.weight.to(ureg.pound)
            return f"{converted.magnitude:.2f} lb"
        return None

# Example output:
# {
#     "id": 1,
#     "name": "Sample Weight",
#     "weight": "Quantity(1000.00 gram)",
#     "weight_in_kg": "1.00 kg",
#     "weight_in_lbs": "2.20 lb"
# }
```

#### ViewSet Example

Here's a complete example showing how to use the serializer in a ViewSet:

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_pint_field.units import ureg

class WeightViewSet(viewsets.ModelViewSet):
    queryset = WeightModel.objects.all()
    serializer_class = WeightSerializer

    @action(detail=True, methods=['get'])
    def convert(self, request, pk=None):
        instance = self.get_object()
        unit = request.query_params.get('unit', 'gram')

        try:
            converted = instance.weight.to(getattr(ureg, unit))
            return Response({
                'original': str(instance.weight),
                'converted': str(converted)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

### Error Handling

The serializer fields include built-in validation and error handling:

- Invalid magnitude values will raise a validation error
- Undefined units will raise a validation error
- Incompatible unit conversions will raise a validation error
- Missing required fields will raise a validation error

Example error responses:

```python
# Invalid magnitude
{
    "weight": ["Invalid magnitude value."]
}

# Invalid units
{
    "weight": ["Invalid or undefined unit."]
}

# Incompatible units
{
    "weight": ["Cannot convert from meters to grams"]
}
```

### Recommended Usage

1. Use `PintRestField` when:

   - You need a more structured, explicit format
   - Working with APIs where the data structure is more important than human readability
   - Dealing with front-end applications that expect consistent JSON structures

2. Use `IntegerPintRestField` / `DecimalPintRestField` when:
   - You need a more compact, human-readable format
   - Working with APIs where string representation is preferred
   - Dealing with systems that expect string-based representations

## 8. Advanced Topics

### 8.1 Custom Units

Django Pint Field allows you to define and use custom units through Pint's unit registry. This is useful when you need to work with domain-specific units or create derived units for special calculations.

#### Creating Custom Unit Definitions

You can create custom units by defining a new unit registry with your custom units. This should be done in your Django settings or a dedicated units configuration file.

```python
from pint import UnitRegistry

# Create a new registry
custom_ureg = UnitRegistry()

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

For more on defining units, see the [Pint documentation](https://pint.readthedocs.io/en/stable/advanced/defining.html)

#### Registering Custom Units

After defining your custom units, you need to tell Django Pint Field to use your custom registry:

```python
# settings.py

# Set the custom registry as the default for the project
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
```

#### Usage in Models

Once registered, you can use your custom units in your models:

```python
from django.db import models
from django_pint_field.models import DecimalPintField

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    serving_size = DecimalPintField(
        "serving",  # Using our custom base unit
        max_digits=10,
        decimal_places=2,
        unit_choices=["serving", "scoop", "portion", "halfserving"]
    )
    energy_density = DecimalPintField(
        "calorie_density",  # Using our custom derived unit
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.name
```

### 8.2 Unit Conversion

Django Pint Field provides several ways to handle unit conversions, both automatically and manually.

#### Automatic Conversion

The field automatically handles unit conversion when saving to the database and when performing comparisons:

```python
from django_pint_field.units import ureg

# Create an instance with one unit
recipe = Recipe.objects.create(
    name="Smoothie",
    serving_size=ureg.Quantity("2 * scoop")  # Will be converted to base units internally
)

# Query using a different unit
large_recipes = Recipe.objects.filter(
    serving_size__gt=ureg.Quantity("3 * serving")
)

# Access in original units
print(recipe.serving_size)  # Outputs: 2 scoop

# Access in different units using properties
print(recipe.serving_size.to("serving"))  # Outputs: 4 serving
print(recipe.serving_size.to("portion"))  # Outputs: 1 portion
```

#### Manual Conversion

You can also perform manual conversions when needed:

```python
from django_pint_field.units import ureg
from decimal import Decimal

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    serving_size = DecimalPintField("serving", max_digits=10, decimal_places=2)

    def get_size_in_unit(self, unit):
        """Convert serving size to specified unit."""
        return self.serving_size.to(unit)

    def scale_recipe(self, scale_factor: Decimal):
        """Scale the recipe by a given factor."""
        return self.serving_size * scale_factor

    def combine_recipes(self, other_recipe):
        """Combine serving sizes of two recipes."""
        return self.serving_size + other_recipe.serving_size

# Usage examples
recipe1 = Recipe.objects.create(name="Small Smoothie", serving_size=ureg.Quantity("1 * scoop"))
recipe2 = Recipe.objects.create(name="Large Smoothie", serving_size=ureg.Quantity("2 * scoop"))

# Manual conversions
print(recipe1.get_size_in_unit("portion"))  # 0.5 portion
print(recipe1.scale_recipe(Decimal("2.5")))  # 2.5 scoop
print(recipe1.combine_recipes(recipe2))  # 3 scoop
```

#### Base Unit Handling

The field uses base units internally for storage and comparison:

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

class WeightMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",  # Base unit
        max_digits=10,
        decimal_places=2,
        unit_choices=["gram", "kilogram", "pound", "ounce"]
    )

    @property
    def base_unit_value(self):
        """Get the value in base units (grams)"""
        return self.weight.to("gram")

    def convert_from_base(self, desired_unit):
        """Convert from base units to desired unit"""
        return self.base_unit_value.to(desired_unit)

    def save(self, *args, **kwargs):
        # Example of pre-save conversion to ensure specific precision
        if self.weight is not None:
            # Convert to base units and round
            in_base = self.weight.to("gram")
            rounded = round(in_base.magnitude, 2)
            self.weight = ureg.Quantity(rounded, "gram")
        super().save(*args, **kwargs)
```

### 8.3 Composite Field Internals

Understanding how Django Pint Field works internally can help you use it more effectively and troubleshoot issues.

#### Field Structure

The field is implemented as a PostgreSQL composite type with three components:

```sql
CREATE TYPE pint_field AS (
    comparator numeric,  -- Magnitude in base units for comparison
    magnitude numeric,   -- Displayed magnitude in user's chosen units
    units text          -- User's chosen units as string
);
```

#### Storage Format

When a value is stored:

1. The original value is preserved in the `magnitude` and `units` fields
2. The value is converted to base units and stored in `comparator`
3. All numeric values are stored as PostgreSQL `numeric` type, allowing us to maintain a high precision.

Example of internal storage:

```python
from django_pint_field.units import ureg

measurement = WeightMeasurement.objects.create(
    weight=ureg.Quantity("2.5 * pound")
)

# Internal representation in database:
# {
#     comparator: 1133.98,  # 2.5 pounds converted to grams
#     magnitude: 2.5,       # Original magnitude
#     units: "pound"        # Original units
# }
```

#### Performance Considerations

1. Indexing:

```python
class WeightMeasurement(models.Model):
    # The comparator component is automatically indexed
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2,
        db_index=True  # This creates an index on the comparator
    )
```

2. Bulk Operations:

```python
from django.db import transaction
from django_pint_field.units import ureg

# Efficient bulk creation
measurements = [
    WeightMeasurement(weight=ureg.Quantity(f"{i} * gram"))
    for i in range(1000)
]

with transaction.atomic():
    WeightMeasurement.objects.bulk_create(
        measurements,
        batch_size=100
    )
```

### 8.4 Unit Registry Management

Understanding how to manage Pint's unit registry in Django is crucial for proper application behavior, especially in multi-threaded environments.

#### Global vs Local Registry Handling

Django Pint Field provides two approaches for managing unit registries:

##### Global Registry (Default)

```python
# settings.py
from pint import UnitRegistry

# Create a single registry for the entire project
DJANGO_PINT_FIELD_UNIT_REGISTER = UnitRegistry()

# Optional: Add custom units to the global registry
DJANGO_PINT_FIELD_UNIT_REGISTER.define("custom_unit = [custom]")
```

##### Local Registry (Per-Module)

```python
# local_units.py
from pint import UnitRegistry

# Create a registry specific to a module
local_ureg = UnitRegistry()
local_ureg.define("module_specific_unit = [custom]")

class LocalRegistryModel(models.Model):
    measurement = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_registry=local_ureg  # Use local registry
    )
```

#### Thread Safety Considerations

Pint's unit registry must be handled carefully in multi-threaded environments:

```python
# safe_registry.py
from django.core.cache import cache
from pint import UnitRegistry
from threading import Lock

class ThreadSafeRegistry:
    _instance = None
    _lock = Lock()

    @classmethod
    def get_registry(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = UnitRegistry()
        return cls._instance

# Usage in views or async code
def async_view(request):
    ureg = ThreadSafeRegistry.get_registry()
    quantity = ureg.Quantity("100 meter")
    # Process quantity...
```

#### Registry Application Context

The registry context affects how quantities are serialized and compared:

```python
from django_pint_field.units import ureg
from pint import set_application_registry, UnitRegistry

# Create application-specific registry
app_registry = UnitRegistry()
app_registry.define("app_specific_unit = [custom]")

# Set as application registry for this context
set_application_registry(app_registry)

class ApplicationSpecificModel(models.Model):
    quantity = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
    )

    def save(self, *args, **kwargs):
        # The quantity will use the application registry
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'my_specific_app'
```

### 8.5 Complex Unit Operations

Django Pint Field supports sophisticated unit operations including derived units, dimensionality validation, and unit system conversions.

#### Handling Derived Units

Derived units combine multiple base units and can be used for complex calculations:

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

class PhysicalMeasurement(models.Model):
    # Basic measurements
    length = DecimalPintField("meter", max_digits=10, decimal_places=2)
    time = DecimalPintField("second", max_digits=10, decimal_places=2)

    # Derived measurements
    velocity = DecimalPintField("meter/second", max_digits=10, decimal_places=2)
    acceleration = DecimalPintField("meter/second**2", max_digits=10, decimal_places=2)

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

#### Unit Dimensionality Validation

Ensure unit compatibility through dimensionality checks:

```python
from django.core.exceptions import ValidationError
from django_pint_field.units import ureg
from django_pint_field.validation import validate_dimensionality

class AreaCalculation(models.Model):
    length = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=["meter", "foot", "yard"]
    )
    width = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=["meter", "foot", "yard"]
    )
    area = DecimalPintField(
        "meter**2",
        max_digits=15,
        decimal_places=2,
        unit_choices=["meter**2", "foot**2", "yard**2"]
    )

    def clean(self):
        if self.length and self.width:
            # Validate dimensionality before calculation
            try:
                result = self.length * self.width
                validate_dimensionality(result, "meter**2")
                self.area = result
            except Exception as e:
                raise ValidationError(f"Area calculation error: {e}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
```

#### Converting Between Unit Systems

Handle conversions between different unit systems (metric, imperial, etc.):

```python
from decimal import Decimal
from django_pint_field.units import ureg

class UnitSystemConverter(models.Model):
    metric_value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=["millimeter", "centimeter", "meter", "kilometer"]
    )
    imperial_value = DecimalPintField(
        "inch",
        max_digits=10,
        decimal_places=2,
        unit_choices=["inch", "foot", "yard", "mile"]
    )

    def convert_to_imperial(self):
        """Convert metric value to imperial"""
        if self.metric_value:
            # Convert to base imperial unit (inches)
            self.imperial_value = self.metric_value.to("inch")

    def convert_to_metric(self):
        """Convert imperial value to metric"""
        if self.imperial_value:
            # Convert to base metric unit (meters)
            self.metric_value = self.imperial_value.to("meter")

    def get_all_conversions(self):
        """Get value in all available units"""
        if self.metric_value:
            base_value = self.metric_value
        elif self.imperial_value:
            base_value = self.imperial_value
        else:
            return None

        return {
            'metric': {
                'mm': base_value.to('millimeter').magnitude,
                'cm': base_value.to('centimeter').magnitude,
                'm': base_value.to('meter').magnitude,
                'km': base_value.to('kilometer').magnitude,
            },
            'imperial': {
                'in': base_value.to('inch').magnitude,
                'ft': base_value.to('foot').magnitude,
                'yd': base_value.to('yard').magnitude,
                'mi': base_value.to('mile').magnitude,
            }
        }

    def round_conversion(self, value, decimals=2):
        """Round converted values to specified decimal places"""
        return Decimal(str(value.magnitude)).quantize(
            Decimal(10) ** -decimals
        ) * value.units
```

Usage example:

```python
# Create a converter instance
converter = UnitSystemConverter(
    metric_value=ureg.Quantity("5.0 * kilometer")
)

# Convert to imperial
converter.convert_to_imperial()
print(converter.imperial_value)  # Outputs: 16404.199475065617 inch

# Get all conversions
conversions = converter.get_all_conversions()
print(conversions)
# Output:
# {
#     'metric': {
#         'mm': 5000000.0,
#         'cm': 500000.0,
#         'm': 5000.0,
#         'km': 5.0
#     },
#     'imperial': {
#         'in': 196850.393700787,
#         'ft': 16404.199475065617,
#         'yd': 5468.066491688539,
#         'mi': 3.106855961114714
#     }
# }
```

### 8.6 Decimal Handling

Django Pint Field provides precise control over decimal values through various configuration options and handling strategies.

#### Precision Management

Control decimal precision at different levels:

```python
# Global precision setting in settings.py
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 28  # Set project-wide precision

# Model-level precision control
class PreciseWeight(models.Model):
    # Field with specific precision requirements
    weight = DecimalPintField(
        "gram",
        max_digits=10,  # Total number of digits
        decimal_places=4,  # Decimal places to maintain
        unit_choices=["gram", "kilogram", "pound"]
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(weight__isnull=False),
                name="weight_not_null"
            )
        ]
```

#### Rounding Strategies

Implement different rounding approaches based on your needs:

```python
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_CEILING
from django_pint_field.units import ureg

class WeightMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2,
        rounding_method=ROUND_HALF_UP  # Default rounding method
    )

    def round_weight(self, method=ROUND_HALF_UP, places=2):
        """Round weight using specified method and decimal places"""
        if self.weight:
            magnitude = Decimal(str(self.weight.magnitude))
            rounded = magnitude.quantize(
                Decimal('0.01'),
                rounding=method
            )
            return ureg.Quantity(rounded, self.weight.units)
        return None

    def get_rounded_weights(self):
        """Get weight rounded using different methods"""
        return {
            'half_up': self.round_weight(ROUND_HALF_UP),
            'down': self.round_weight(ROUND_DOWN),
            'ceiling': self.round_weight(ROUND_CEILING),
        }
```

#### Decimal Context Configuration

Manage decimal context for precise calculations:

```python
from decimal import getcontext, localcontext
from django_pint_field.units import ureg

class HighPrecisionMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=20,
        decimal_places=10
    )

    def precise_calculation(self):
        """Perform high-precision calculations"""
        with localcontext() as ctx:
            # Temporarily set higher precision for this calculation
            ctx.prec = 50

            if self.value:
                # Perform precise calculation
                result = (self.value ** 2).magnitude
                # Return with original precision
                return Decimal(str(result)).quantize(
                    Decimal('0.0000000001')
                )

    @staticmethod
    def set_global_precision(precision):
        """Set global decimal precision"""
        getcontext().prec = precision
```

Below is a portion of our usage guide for this package. Following it as an example, please provide one or more new sections about using the `PintFieldComparatorIndex` after "##### Basic Django Indexes in the Model Meta Class".

### 8.7 Database Optimization

Optimize database performance when working with Django Pint Fields through various strategies.

#### Index Strategies for Composite Fields

Implement efficient indexing for better query performance:

##### Basic Django Indexes on the Field

```python
from django.db import models
from django_pint_field.models import DecimalPintField

class OptimizedMeasurement(models.Model):
    simple_value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        db_index=True
    )
```

##### Basic Django Indexes in the Model Meta Class

```python
from django.db import models
from django_pint_field.models import DecimalPintField

class OptimizedMeasurement(models.Model):
    complex_value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        indexes = [
            models.Index(
                fields=['complex_value'],
                name='complex_value_idx'
            )
        ]
```

##### Optimized Indexing with PintFieldComparatorIndex

`PintFieldComparatorIndex` provides specialized indexing for the `comparator` component of Pint fields, enabling efficient querying and filtering:

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.indexes import PintFieldComparatorIndex

class OptimizedMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2
    )
    height = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        indexes = [
            # Single field index
            PintFieldComparatorIndex(fields=['weight']),

            # Multi-field composite index
            PintFieldComparatorIndex(
                fields=['weight', 'height'],
                name='measurement_weight_height_idx'
            )
        ]
```

##### Advanced PintFieldComparatorIndex Features

The `PintFieldComparatorIndex` supports several advanced indexing features:

```python
class AdvancedMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2
    )
    volume = DecimalPintField(
        "liter",
        max_digits=10,
        decimal_places=2
    )
    temperature = DecimalPintField(
        "celsius",
        max_digits=6,
        decimal_places=2
    )

    class Meta:
        indexes = [
            # Partial index for positive weights
            PintFieldComparatorIndex(
                fields=['weight'],
                condition='(weight).magnitude > 0',
                name='positive_weight_idx'
            ),

            # Covering index including additional columns
            PintFieldComparatorIndex(
                fields=['volume'],
                include=['id', 'temperature'],
                name='volume_covering_idx'
            ),

            # Multi-field index with custom tablespace
            PintFieldComparatorIndex(
                fields=['weight', 'volume'],
                db_tablespace='measurement_space',
                name='weight_volume_space_idx'
            )
        ]
```

Optimize queries by leveraging the specialized indexes above

```python
from django.db.models import F, Q
from django_pint_field.units import ureg

class IndexedQueryOptimizer:
    @staticmethod
    def efficient_multi_field_query(
        min_weight,
        max_weight,
        min_height,
        max_height
    ):
        """Efficient range query using multi-field index."""
        # Convert input values to base units
        min_weight_base = ureg.Quantity(min_weight, "gram").to_base_units()
        max_weight_base = ureg.Quantity(max_weight, "gram").to_base_units()
        min_height_base = ureg.Quantity(min_height, "meter").to_base_units()
        max_height_base = ureg.Quantity(max_height, "meter").to_base_units()

        return OptimizedMeasurement.objects.filter(
            Q(weight__gte=min_weight_base) &
            Q(weight__lte=max_weight_base) &
            Q(height__gte=min_height_base) &
            Q(height__lte=max_height_base)
        ).order_by('weight', 'height')  # Will use multi-field index

    @staticmethod
    def covering_index_query():
        """Query utilizing covering index to avoid table lookups."""
        return AdvancedMeasurement.objects.filter(
            volume__gt=ureg.Quantity('1 liter')
        ).values('id', 'temperature')  # Uses covering index

    @staticmethod
    def partial_index_query():
        """Query leveraging partial index for positive weights."""
        return AdvancedMeasurement.objects.filter(
            weight__gt=ureg.Quantity('0 gram')
        ).order_by('weight')  # Will use partial index
```

##### Performance Considerations for PintFieldComparatorIndex

Best practices when using composite field indexes:

```python
# 1. Match index order in queries
measurements = OptimizedMeasurement.objects.filter(
    weight__gt=ureg.Quantity('100 gram'),
    height__gt=ureg.Quantity('1 meter')
).order_by('weight', 'height')  # Matches index order defined in the index

# 2. Use covering indexes for frequently accessed fields
frequent_queries = AdvancedMeasurement.objects.filter(
    volume__gt=ureg.Quantity('2 liter')
).values('id', 'temperature')  # Uses covering index

# 3. Leverage partial indexes for filtered queries
positive_weights = AdvancedMeasurement.objects.filter(
    weight__gt=ureg.Quantity('0 gram')
).order_by('weight')  # Uses partial index

# 4. Consider index size vs query performance.
#    Here is an example to get basic info on index size.
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT pg_size_pretty(pg_total_relation_size('measurement_weight_height_idx'));
    """)
    index_size = cursor.fetchone()[0]
```

Remember:

- Multi-field indexes are most effective when all indexed fields are used in queries
- Indexes can significantly improve performance but increase storage requirements
- Partial indexes reduce index size while maintaining performance for specific queries
- Monitor index usage and size to ensure optimal performance

#### Bulk Operation Patterns

Implement efficient bulk operations:

```python
from django.db import transaction
from django_pint_field.units import ureg
from typing import List

class BulkOperationHandler:
    @staticmethod
    def bulk_create_measurements(data: List[dict], batch_size=1000):
        """Efficient bulk creation of measurements."""
        measurements = []

        for item in data:
            measurement = OptimizedMeasurement(
                simple_value=ureg.Quantity(
                    item['value'],
                    item['unit']
                )
            )
            measurements.append(measurement)

            if len(measurements) >= batch_size:
                with transaction.atomic():
                    OptimizedMeasurement.objects.bulk_create(
                        measurements,
                        batch_size=batch_size
                    )
                measurements = []

        # Create any remaining measurements
        if measurements:
            with transaction.atomic():
                OptimizedMeasurement.objects.bulk_create(
                    measurements,
                    batch_size=batch_size
                )

    @staticmethod
    def bulk_update_measurements(
        queryset,
        new_value: ureg.Quantity,
        batch_size=1000
    ):
        """Efficient bulk update of measurements."""
        with transaction.atomic():
            for instance in queryset.iterator(chunk_size=batch_size):
                instance.simple_value = new_value

            OptimizedMeasurement.objects.bulk_update(
                queryset,
                ['simple_value'],
                batch_size=batch_size
            )

    @staticmethod
    def optimized_deletion(criteria: dict):
        """Efficient deletion with criteria."""
        with transaction.atomic():
            OptimizedMeasurement.objects.filter(
                **criteria
            ).delete()

# Usage examples
handler = BulkOperationHandler()

# Bulk create
data = [
    {'value': 10, 'unit': 'meter'},
    {'value': 20, 'unit': 'meter'},
    # ... more data
]
handler.bulk_create_measurements(data)

# Bulk update
queryset = OptimizedMeasurement.objects.filter(
    simple_value__lt=ureg.Quantity('15 meter')
)
handler.bulk_update_measurements(
    queryset,
    ureg.Quantity('15 meter')
)

# Optimized deletion
handler.optimized_deletion({
    'simple_value__lt': ureg.Quantity('5 meter')
})
```

## 9. Best Practices and Tips

### 9.1 Performance Optimization

Optimize your Django Pint Field implementation for better performance and resource utilization.

#### Query Optimization

Implement efficient querying patterns to minimize database load:

```python
from django.db.models import F, Q, Prefetch
from django_pint_field.units import ureg
from django_pint_field.models import DecimalPintField
from django_pint_field.indexes import PintFieldComparatorIndex

class Measurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.PintFieldComparatorIndex(
                fields=['value'],
                name='value_idx',
            )
        ]

### Good - Uses indexed comparator field
Measurement.objects.filter(
    value__gte=ureg.Quantity('10 meter')
).select_related()

### Good - Combines multiple conditions
Measurement.objects.filter(
    Q(value__gte=ureg.Quantity('10 meter')) &
    Q(value__lte=ureg.Quantity('20 meter'))
).select_related()

### Bad - Performs conversion in Python
[m for m in Measurement.objects.all() if m.value.to('feet').magnitude > 32.8]

### Good - Performs conversion in database
Measurement.objects.filter(
    value__gt=ureg.Quantity('10 meter').to('meter')
)
```

#### Bulk Operations

Use bulk operations for better performance when handling multiple records:

```python
from django.db import transaction
from typing import List

class BulkMeasurementHandler:
    @staticmethod
    def create_measurements(data: List[dict], batch_size: int = 1000) -> None:
        """Efficiently create multiple measurements"""
        measurements = [
            Measurement(
                value=ureg.Quantity(item['value'], item['unit'])
            )
            for item in data
        ]

        with transaction.atomic():
            Measurement.objects.bulk_create(
                measurements,
                batch_size=batch_size
            )

    @staticmethod
    def update_measurements(
        queryset,
        new_value: ureg.Quantity,
        batch_size: int = 1000
    ) -> None:
        """Efficiently update multiple measurements"""
        with transaction.atomic():
            queryset.update(value=new_value)

### Usage
handler = BulkMeasurementHandler()
data = [
    {'value': 10, 'unit': 'meter'},
    {'value': 20, 'unit': 'meter'},
    # ... more data
]
handler.create_measurements(data)
```

#### Caching Considerations

Implement caching strategies to improve performance:

```python
from django.core.cache import cache
from django.db import models
from django_pint_field.models import DecimalPintField
from typing import Optional

class CachedMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
    )

    def get_cached_conversion(
        self,
        unit: str,
        timeout: int = 3600
    ) -> Optional[ureg.Quantity]:
        """Get or cache converted value"""
        cache_key = f"measurement_{self.pk}_{unit}"
        cached_value = cache.get(cache_key)

        if cached_value is None and self.value is not None:
            converted = self.value.to(unit)
            cache.set(cache_key, converted, timeout)
            return converted

        return cached_value

    def clear_conversion_cache(self) -> None:
        """Clear cached conversions"""
        cache.delete_pattern(f"measurement_{self.pk}_*")

    def save(self, *args, **kwargs):
        """Clear cache on save"""
        self.clear_conversion_cache()
        super().save(*args, **kwargs)
```

### 9.2 Common Patterns

Follow these common patterns for consistent and maintainable code.

#### Validation Strategies

Implement robust validation patterns:

```python
from django.core.exceptions import ValidationError
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg

class ValidatedMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=["meter", "kilometer", "mile"]
    )

    def clean(self) -> None:
        """Validate measurement"""
        if self.value is not None:
            # Validate range
            if self.value.to('meter').magnitude > 1000000:
                raise ValidationError(
                    "Value cannot exceed 1,000,000 meters"
                )

            # Validate dimensionality
            if self.value.dimensionality != ureg.meter.dimensionality:
                raise ValidationError(
                    "Invalid unit dimensionality"
                )

    def save(self, *args, **kwargs) -> None:
        """Save with validation"""
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_valid_units(cls) -> list:
        """Get list of valid units"""
        field = cls._meta.get_field('value')
        return field.unit_choices
```

#### Unit Conversion Patterns

Standardize unit conversion approaches:

```python
from typing import Dict, Any
from decimal import Decimal

class ConversionMixin:
    """Mixin for common conversion patterns"""

    def to_unit(
        self,
        unit: str,
        round_digits: int = 2
    ) -> ureg.Quantity:
        """Convert to specified unit with rounding"""
        if self.value is None:
            return None

        converted = self.value.to(unit)
        magnitude = Decimal(str(converted.magnitude))
        rounded = round(magnitude, round_digits)
        return ureg.Quantity(rounded, unit)

    def get_all_units(self) -> Dict[str, Any]:
        """Get value in all available units"""
        if self.value is None:
            return {}

        return {
            unit: self.to_unit(unit)
            for unit in self.get_valid_units()
        }

    def format_value(
        self,
        unit: Optional[str] = None,
        decimal_places: int = 2
    ) -> str:
        """Format value for display"""
        if self.value is None:
            return ""

        value = self.to_unit(unit) if unit else self.value
        return f"{value.magnitude:.{decimal_places}f} {value.units}"

class EnhancedMeasurement(ConversionMixin, ValidatedMeasurement):
    class Meta:
        proxy = True
```

#### Error Handling

Implement consistent error handling patterns:

```python
from django.core.exceptions import ValidationError
from typing import Optional, Union

class MeasurementError(Exception):
    """Base exception for measurement errors"""
    pass

class UnitConversionError(MeasurementError):
    """Error for unit conversion issues"""
    pass

class MeasurementHandler:
    """Handler for safe measurement operations"""

    @staticmethod
    def safe_convert(
        value: ureg.Quantity,
        target_unit: str
    ) -> Optional[ureg.Quantity]:
        """Safely convert between units"""
        try:
            return value.to(target_unit)
        except Exception as e:
            raise UnitConversionError(
                f"Could not convert {value} to {target_unit}: {str(e)}"
            )

    @staticmethod
    def safe_create(
        value: Union[float, int, Decimal],
        unit: str
    ) -> ureg.Quantity:
        """Safely create a quantity"""
        try:
            return ureg.Quantity(value, unit)
        except Exception as e:
            raise MeasurementError(
                f"Could not create quantity with {value} {unit}: {str(e)}"
            )

class SafeMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
    )

    def convert_value(
        self,
        target_unit: str
    ) -> Optional[ureg.Quantity]:
        """Safely convert measurement value"""
        if self.value is None:
            return None

        try:
            return MeasurementHandler.safe_convert(
                self.value,
                target_unit
            )
        except UnitConversionError as e:
            logger.error(f"Conversion error: {e}")
            return None
```

### 9.3 Troubleshooting

A great first place to look when experiencing issues with conversions, units, Quantity objects, etc is the [Pint documentation](https://pint.readthedocs.io/en/stable/).

#### Common Issues

1. Unit Compatibility Issues:

```python
from django_pint_field.helpers import check_matching_unit_dimension

def validate_unit_compatibility(value: ureg.Quantity, base_unit: str) -> bool:
    """Check if units are compatible"""
    try:
        check_matching_unit_dimension(
            ureg,
            base_unit,
            [str(value.units)]
        )
        return True
    except ValidationError:
        return False

### Usage
measurement = Measurement(value=ureg.Quantity("100 gram"))
is_compatible = validate_unit_compatibility(
    measurement.value,
    "meter"
)  # False - incompatible units
```

You can also use `check_matching_unit_dimension` directly.

2. Precision Loss:

Unlike `float` values, with `Decimal` values we do not use Python's `round` function. Instead, we should [quantize](https://docs.python.org/3/library/decimal.html#decimal.Decimal.quantize) the value, which more appropriately truncates (and optionally [rounds](https://docs.python.org/3/library/decimal.html#rounding-modes)) the Decimal value.

```python
from decimal import Decimal, ROUND_HALF_UP

def preserve_precision(
    value: ureg.Quantity,
    decimal_places: int = 2
) -> ureg.Quantity:
    """Preserve decimal precision"""
    if value is None:
        return None

    magnitude = Decimal(str(value.magnitude))
    rounded = magnitude.quantize(
        Decimal(f"0.{'0' * decimal_places}"),
        rounding=ROUND_HALF_UP
    )
    return ureg.Quantity(rounded, value.units)
```

#### Debug Strategies

1. Value Inspection:

```python
class DebugMeasurement(models.Model):
    value = DecimalPintField(
        default_unit="meter",
        max_digits=10,
        decimal_places=2
    )

    def debug_info(self) -> dict:
        """Get detailed debug information"""
        if self.value is None:
            return {'error': 'No value set'}

        return {
            'magnitude': self.value.magnitude,
            'units': str(self.value.units),
            'dimensionality': str(self.value.dimensionality),
            'base_value': self.value.to_base_units(),
            'valid_units': self.get_valid_units()
        }
```

2. Query Logging:

```python
import logging
from django.db import connection

logger = logging.getLogger(__name__)

def log_queries(func):
    """Decorator to log queries"""
    def wrapper(*args, **kwargs):
        queries_before = len(connection.queries)
        result = func(*args, **kwargs)
        queries_after = len(connection.queries)

        logger.debug(
            f"Function {func.__name__} executed "
            f"{queries_after - queries_before} queries"
        )

        for query in connection.queries[queries_before:]:
            logger.debug(f"Query: {query['sql']}")

        return result
    return wrapper

@log_queries
def fetch_measurements():
    return Measurement.objects.filter(
        value__gt=ureg.Quantity('10 meter')
    )
```

3. Validation Testing:

```python
from django.test import TestCase

class MeasurementTests(TestCase):
    def test_unit_conversion(self):
        """Test unit conversion accuracy"""
        measurement = Measurement.objects.create(
            value=ureg.Quantity('1000 meter')
        )

        # Test conversion to kilometers
        km_value = measurement.value.to('kilometer')
        self.assertEqual(km_value.magnitude, 1)

        # Test conversion to miles
        mile_value = measurement.value.to('mile')
        self.assertAlmostEqual(
            mile_value.magnitude,
            0.621371,
            places=6
        )
```

### 9.4 Edge Cases

Handle special cases and extreme values appropriately.

#### Handling Very Large/Small Quantities

```python
from decimal import Decimal
from django_pint_field.models import DecimalPintField
from typing import Optional

class ExtremeMeasurement(models.Model):
    """Model for handling extreme values"""

    value = DecimalPintField(
        default_unit="meter",
        max_digits=30,  # Large precision for extreme values
        decimal_places=15
    )

    def format_scientific(
        self,
        decimal_places: int = 2
    ) -> str:
        """Format in scientific notation"""
        if self.value is None:
            return ""

        magnitude = self.value.magnitude
        if isinstance(magnitude, Decimal):
            # Format as scientific notation
            return f"{magnitude:.{decimal_places}E} {self.value.units}"
        return str(self.value)

    def get_human_readable(self) -> str:
        """Get human-readable format with appropriate unit"""
        if self.value is None:
            return ""

        # List of unit prefixes from smallest to largest
        prefixes = [
            ('femto', 1e-15),
            ('pico', 1e-12),
            ('nano', 1e-9),
            ('micro', 1e-6),
            ('milli', 1e-3),
            ('', 1),
            ('kilo', 1e3),
            ('mega', 1e6),
            ('giga', 1e9),
            ('tera', 1e12),
            ('peta', 1e15)
        ]

        magnitude = float(self.value.magnitude)
        base_unit = str(self.value.units)

        # Find appropriate prefix
        for prefix, scale in reversed(prefixes):
            if abs(magnitude) >= scale:
                converted = magnitude / scale
                return f"{converted:.2f} {prefix}{base_unit}"

        return str(self.value)
```

#### Zero and Negative Values

```python
class SignAwareMeasurement(models.Model):
    """Model handling zero and negative values"""

    value = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2
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
        """Get value sign"""
        if self.value is None:
            return None

        return 1 if self.value.magnitude > 0 else -1 if self.value.magnitude < 0 else 0
```

## 10. Migration and Deployment

### 10.1 Database Considerations

When working with Django Pint Field in production environments, there are several important database considerations to keep in mind.

#### PostgreSQL Requirements

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        # Required settings for django-pint-field
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}

# Ensure pint_field composite type is available
INSTALLED_APPS = [
    # ...
    'django_pint_field',
    # ...
]
```

#### Migration Handling

```python
# migrations.py
from django.db import migrations
from django_pint_field.models import DecimalPintField

class Migration(migrations.Migration):
    """Safe migration for PintField"""

    dependencies = [
        ('your_app', '0001_initial'),
    ]

    def migrate_units_forward(apps, schema_editor):
        """Convert values to new units"""
        YourModel = apps.get_model('your_app', 'YourModel')
        for instance in YourModel.objects.all():
            if instance.measurement is not None:
                # Convert to new unit
                instance.measurement = instance.measurement.to('new_unit')
                instance.save()

    def migrate_units_backward(apps, schema_editor):
        """Revert to original units"""
        YourModel = apps.get_model('your_app', 'YourModel')
        for instance in YourModel.objects.all():
            if instance.measurement is not None:
                # Convert back to original unit
                instance.measurement = instance.measurement.to('original_unit')
                instance.save()

    operations = [
        migrations.RunPython(
            migrate_units_forward,
            migrate_units_backward
        ),
    ]
```

#### Backup Considerations

```python
# backup_handler.py
from django.core.management.base import BaseCommand
from django.db import connection
from decimal import Decimal
from typing import Dict, Any
import json

class PintFieldBackupHandler(BaseCommand):
    """Handler for backing up PintField data"""

    help = 'Backup and restore PintField data'

    def serialize_quantity(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize Quantity objects for backup"""
        for field, value in obj.items():
            if hasattr(value, 'magnitude') and hasattr(value, 'units'):
                obj[field] = {
                    'magnitude': str(value.magnitude),
                    'units': str(value.units),
                    'comparator': str(value.to_base_units().magnitude)
                }
        return obj

    def deserialize_quantity(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize Quantity objects from backup"""
        for field, value in obj.items():
            if isinstance(value, dict) and all(k in value for k in ['magnitude', 'units']):
                obj[field] = {
                    'magnitude': Decimal(value['magnitude']),
                    'units': value['units'],
                    'comparator': Decimal(value['comparator'])
                }
        return obj

    def backup_data(self, model, file_path: str) -> None:
        """Backup model data with PintFields"""
        with open(file_path, 'w') as f:
            objects = model.objects.all()
            serialized_objects = [
                self.serialize_quantity(obj.__dict__)
                for obj in objects
            ]
            json.dump(serialized_objects, f, indent=2)

    def restore_data(self, model, file_path: str) -> None:
        """Restore model data with PintFields"""
        with open(file_path, 'r') as f:
            objects = json.load(f)
            for obj_data in objects:
                deserialized_data = self.deserialize_quantity(obj_data)
                model.objects.create(**deserialized_data)
```

### 10.2 Production Setup

#### Monitoring Tips

```python
# monitoring.py
import logging
from django.db import connection
from django.db.models import Count
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class PintFieldMonitor:
    """Monitor PintField operations and performance"""

    @staticmethod
    def log_conversion_time(func):
        """Decorator to log conversion times"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                'Unit conversion took %.3f seconds',
                duration
            )
            return result
        return wrapper

    @staticmethod
    def get_field_statistics(model) -> Dict[str, Any]:
        """Get statistics for PintField usage"""
        stats = {
            'total_records': model.objects.count(),
            'null_values': model.objects.filter(
                value__isnull=True
            ).count(),
            'unique_units': model.objects.values(
                'value__units'
            ).distinct().count()
        }

        # Get unit distribution
        unit_distribution = model.objects.values(
            'value__units'
        ).annotate(
            count=Count('id')
        )

        stats['unit_distribution'] = {
            item['value__units']: item['count']
            for item in unit_distribution
        }

        return stats
```

These monitoring tools can be used in conjunction with external monitoring services:

```python
# Example integration with Sentry
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,

    # Enable performance monitoring
    enable_tracing=True,
)

# Custom Sentry breadcrumb for PintField operations
def log_pint_operation(operation: str, data: Dict[str, Any]) -> None:
    sentry_sdk.add_breadcrumb(
        category='pint_field',
        message=f'PintField operation: {operation}',
        data=data,
        level='info'
    )
```

Remember to monitor:

- Conversion performance
- Database query patterns
- Error rates
- Cache hit rates
- Memory usage
- Database connection pooling
- Index usage statistics
