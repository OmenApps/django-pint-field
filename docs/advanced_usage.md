# Advanced Usage

## 1. REST Framework Integration

Django Pint Field provides seamless integration with Django REST Framework (DRF) through specialized serializer fields. This integration allows you to serialize and deserialize Pint quantities in your API endpoints while maintaining unit consistency and proper validation.

### 1.1 Serializer Fields

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
{"magnitude": 1.5, "units": "gram"}
```

### 1.2 Serializer Examples

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
        fields = ["id", "name", "weight", "precise_weight"]
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
        fields = ["id", "name", "weight", "precise_weight"]


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
        fields = ["id", "name", "weight"]


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
        fields = ["id", "name", "weight"]

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
        fields = [
            "id",
            "name",
            "weight",
            "weight_in_kg",
            "weight_in_lbs",
        ]

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

    @action(detail=True, methods=["get"])
    def convert(self, request, pk=None):
        instance = self.get_object()
        unit = request.query_params.get("unit", "gram")

        try:
            converted = instance.weight.to(getattr(ureg, unit))
            return Response(
                {"original": str(instance.weight), "converted": str(converted)}
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)
```

### 1.3 Error Handling

The serializer fields include built-in validation and error handling:

- Invalid magnitude values will raise a validation error
- Undefined units will raise a validation error
- Incompatible unit conversions will raise a validation error
- Missing required fields will raise a validation error

Example error responses:

```python
# Invalid magnitude
{"weight": ["Invalid magnitude value."]}

# Invalid units
{"weight": ["Invalid or undefined unit."]}

# Incompatible units
{"weight": ["Cannot convert from meters to grams"]}
```

### 1.4 Recommended Usage

1. Use `PintRestField` when:

   - You need a more structured, explicit format
   - Working with APIs where the data structure is more important than human readability
   - Dealing with front-end applications that expect consistent JSON structures

2. Use `IntegerPintRestField` / `DecimalPintRestField` when:
   - You need a more compact, human-readable format
   - Working with APIs where string representation is preferred
   - Dealing with systems that expect string-based representations

## 2. Advanced Topics

### 2.1 Custom Units

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
        unit_choices=[
            "serving",
            "scoop",
            "portion",
            "halfserving",
        ],
    )
    energy_density = DecimalPintField(
        "calorie_density",  # Using our custom derived unit
        max_digits=10,
        decimal_places=2,
    )

    def __str__(self):
        return self.name
```

### 2.2 Unit Conversion

Django Pint Field provides several ways to handle unit conversions, both automatically and manually.

#### Automatic Conversion

The field automatically handles unit conversion when saving to the database and when performing comparisons:

```python
from django_pint_field.units import ureg

# Create an instance with one unit
recipe = Recipe.objects.create(
    name="Smoothie",
    serving_size=ureg.Quantity(
        "2 * scoop"
    ),  # Will be converted to base units internally
)

# Query using a different unit
large_recipes = Recipe.objects.filter(
    serving_size__gt=ureg.Quantity("3 * serving"),
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
    serving_size = DecimalPintField(
        "serving",
        max_digits=10,
        decimal_places=2,
    )

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
recipe1 = Recipe.objects.create(
    name="Small Smoothie", serving_size=ureg.Quantity("1 * scoop")
)
recipe2 = Recipe.objects.create(
    name="Large Smoothie", serving_size=ureg.Quantity("2 * scoop")
)

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
        unit_choices=[
            "gram",
            "kilogram",
            "pound",
            "ounce",
        ],
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

### 2.3 Composite Field Internals

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
    weight=ureg.Quantity("2.5 * pound"),
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
        db_index=True,  # This creates an index on the comparator
    )
```

2. Bulk Operations:

```python
from django.db import transaction
from django_pint_field.units import ureg

# Efficient bulk creation
measurements = [
    WeightMeasurement(weight=ureg.Quantity(f"{i} * gram")) for i in range(1000)
]

with transaction.atomic():
    WeightMeasurement.objects.bulk_create(
        measurements,
        batch_size=100,
    )
```

### 2.4 Unit Registry Management

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
        unit_registry=local_ureg,  # Use local registry
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
        decimal_places=2,
    )

    def save(self, *args, **kwargs):
        # The quantity will use the application registry
        super().save(*args, **kwargs)

    class Meta:
        app_label = "my_specific_app"
```

### 2.5 Complex Unit Operations

Django Pint Field supports sophisticated unit operations including derived units, dimensionality validation, and unit system conversions.

#### Handling Derived Units

Derived units combine multiple base units and can be used for complex calculations:

```python
from django.db import models
from django_pint_field.models import DecimalPintField
from django_pint_field.units import ureg


class PhysicalMeasurement(models.Model):
    # Basic measurements
    length = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
    )
    time = DecimalPintField(
        "second",
        max_digits=10,
        decimal_places=2,
    )

    # Derived measurements
    velocity = DecimalPintField(
        "meter/second",
        max_digits=10,
        decimal_places=2,
    )
    acceleration = DecimalPintField(
        "meter/second**2",
        max_digits=10,
        decimal_places=2,
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
        unit_choices=["meter", "foot", "yard"],
    )
    width = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
        unit_choices=["meter", "foot", "yard"],
    )
    area = DecimalPintField(
        "meter**2",
        max_digits=15,
        decimal_places=2,
        unit_choices=[
            "meter**2",
            "foot**2",
            "yard**2",
        ],
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
        unit_choices=[
            "millimeter",
            "centimeter",
            "meter",
            "kilometer",
        ],
    )
    imperial_value = DecimalPintField(
        "inch",
        max_digits=10,
        decimal_places=2,
        unit_choices=["inch", "foot", "yard", "mile"],
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

Usage example:

```python
# Create a converter instance
converter = UnitSystemConverter(metric_value=ureg.Quantity("5.0 * kilometer"))

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

### 2.6 Decimal Handling

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

#### Decimal Context Configuration

Manage decimal context for precise calculations:

```python
from decimal import getcontext, localcontext
from django_pint_field.units import ureg


class HighPrecisionMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        max_digits=20,
        decimal_places=10,
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

Below is a portion of our usage guide for this package. Following it as an example, please provide one or more new sections about using the `PintFieldComparatorIndex` after "##### Basic Django Indexes in the Model Meta Class".

### 2.7 Database Optimization

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
        db_index=True,
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
        decimal_places=2,
    )

    class Meta:
        indexes = [
            models.Index(fields=["complex_value"], name="complex_value_idx"),
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
        decimal_places=2,
    )
    height = DecimalPintField(
        "meter",
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        indexes = [
            # Single field index
            PintFieldComparatorIndex(fields=["weight"]),
            # Multi-field composite index
            PintFieldComparatorIndex(
                fields=["weight", "height"],
                name="measurement_weight_height_idx",
            ),
        ]
```

##### Advanced PintFieldComparatorIndex Features

The `PintFieldComparatorIndex` supports several advanced indexing features:

```python
class AdvancedMeasurement(models.Model):
    weight = DecimalPintField(
        "gram",
        max_digits=10,
        decimal_places=2,
    )
    volume = DecimalPintField(
        "liter",
        max_digits=10,
        decimal_places=2,
    )
    temperature = DecimalPintField(
        "celsius",
        max_digits=6,
        decimal_places=2,
    )

    class Meta:
        indexes = [
            # Partial index for positive weights
            PintFieldComparatorIndex(
                fields=["weight"],
                condition="(weight).magnitude > 0",
                name="positive_weight_idx",
            ),
            # Covering index including additional columns
            PintFieldComparatorIndex(
                fields=["volume"],
                include=["id", "temperature"],
                name="volume_covering_idx",
            ),
            # Multi-field index with custom tablespace
            PintFieldComparatorIndex(
                fields=["weight", "volume"],
                db_tablespace="measurement_space",
                name="weight_volume_space_idx",
            ),
        ]
```

Optimize queries by leveraging the specialized indexes above

```python
from django.db.models import F, Q
from django_pint_field.units import ureg


class IndexedQueryOptimizer:
    @staticmethod
    def efficient_multi_field_query(min_weight, max_weight, min_height, max_height):
        """Efficient range query using multi-field index."""
        # Convert input values to base units
        min_weight_base = ureg.Quantity(min_weight, "gram").to_base_units()
        max_weight_base = ureg.Quantity(max_weight, "gram").to_base_units()
        min_height_base = ureg.Quantity(min_height, "meter").to_base_units()
        max_height_base = ureg.Quantity(max_height, "meter").to_base_units()

        return OptimizedMeasurement.objects.filter(
            Q(weight__gte=min_weight_base)
            & Q(weight__lte=max_weight_base)
            & Q(height__gte=min_height_base)
            & Q(height__lte=max_height_base)
        ).order_by(
            "weight", "height"
        )  # Will use multi-field index

    @staticmethod
    def covering_index_query():
        """Query utilizing covering index to avoid table lookups."""
        return AdvancedMeasurement.objects.filter(
            volume__gt=ureg.Quantity("1 liter")
        ).values(
            "id", "temperature"
        )  # Uses covering index

    @staticmethod
    def partial_index_query():
        """Query leveraging partial index for positive weights."""
        return AdvancedMeasurement.objects.filter(
            weight__gt=ureg.Quantity("0 gram")
        ).order_by(
            "weight"
        )  # Will use partial index
```

##### Performance Considerations for PintFieldComparatorIndex

Best practices when using composite field indexes:

```python
# 1. Match index order in queries
measurements = OptimizedMeasurement.objects.filter(
    weight__gt=ureg.Quantity("100 gram"),
    height__gt=ureg.Quantity("1 meter"),
).order_by(
    "weight", "height"
)  # Matches index order defined in the index

# 2. Use covering indexes for frequently accessed fields
frequent_queries = AdvancedMeasurement.objects.filter(
    volume__gt=ureg.Quantity("2 liter")
).values(
    "id", "temperature"
)  # Uses covering index

# 3. Leverage partial indexes for filtered queries
positive_weights = AdvancedMeasurement.objects.filter(
    weight__gt=ureg.Quantity("0 gram")
).order_by(
    "weight"
)  # Uses partial index

# 4. Consider index size vs query performance.
#    Here is an example to get basic info on index size.
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        """
        SELECT pg_size_pretty(pg_total_relation_size('measurement_weight_height_idx'));
    """
    )
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
                simple_value=ureg.Quantity(item["value"], item["unit"])
            )
            measurements.append(measurement)

            if len(measurements) >= batch_size:
                with transaction.atomic():
                    OptimizedMeasurement.objects.bulk_create(
                        measurements, batch_size=batch_size
                    )
                measurements = []

        # Create any remaining measurements
        if measurements:
            with transaction.atomic():
                OptimizedMeasurement.objects.bulk_create(
                    measurements, batch_size=batch_size
                )

    @staticmethod
    def bulk_update_measurements(queryset, new_value: ureg.Quantity, batch_size=1000):
        """Efficient bulk update of measurements."""
        with transaction.atomic():
            for instance in queryset.iterator(chunk_size=batch_size):
                instance.simple_value = new_value

            OptimizedMeasurement.objects.bulk_update(
                queryset, ["simple_value"], batch_size=batch_size
            )

    @staticmethod
    def optimized_deletion(criteria: dict):
        """Efficient deletion with criteria."""
        with transaction.atomic():
            OptimizedMeasurement.objects.filter(**criteria).delete()


# Usage examples
handler = BulkOperationHandler()

# Bulk create
data = [
    {"value": 10, "unit": "meter"},
    {"value": 20, "unit": "meter"},
    # ... more data
]
handler.bulk_create_measurements(data)

# Bulk update
queryset = OptimizedMeasurement.objects.filter(
    simple_value__lt=ureg.Quantity("15 meter")
)
handler.bulk_update_measurements(queryset, ureg.Quantity("15 meter"))

# Optimized deletion
handler.optimized_deletion(
    {"simple_value__lt": ureg.Quantity("5 meter")},
)
```

## 3. Best Practices and Tips

### 3.1 Performance Optimization

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
                fields=["value"],
                name="value_idx",
            )
        ]


### Good - Uses indexed comparator field
Measurement.objects.filter(value__gte=ureg.Quantity("10 meter")).select_related()

### Good - Combines multiple conditions
Measurement.objects.filter(
    Q(
        value__gte=ureg.Quantity("10 meter"),
    )
    & Q(
        value__lte=ureg.Quantity("20 meter"),
    )
).select_related()

### Bad - Performs conversion in Python
[m for m in Measurement.objects.all() if m.value.to("feet").magnitude > 32.8]

### Good - Performs conversion in database
Measurement.objects.filter(
    value__gt=ureg.Quantity("10 meter").to("meter"),
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
            Measurement(value=ureg.Quantity(item["value"], item["unit"]))
            for item in data
        ]

        with transaction.atomic():
            Measurement.objects.bulk_create(measurements, batch_size=batch_size)

    @staticmethod
    def update_measurements(
        queryset, new_value: ureg.Quantity, batch_size: int = 1000
    ) -> None:
        """Efficiently update multiple measurements"""
        with transaction.atomic():
            queryset.update(value=new_value)


### Usage
handler = BulkMeasurementHandler()
data = [
    {"value": 10, "unit": "meter"},
    {"value": 20, "unit": "meter"},
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
        decimal_places=2,
    )

    def get_cached_conversion(
        self, unit: str, timeout: int = 3600
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

### 3.2 Common Patterns

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
        unit_choices=["meter", "kilometer", "mile"],
    )

    def clean(self) -> None:
        """Validate measurement"""
        if self.value is not None:
            # Validate range
            if self.value.to("meter").magnitude > 1000000:
                raise ValidationError("Value cannot exceed 1,000,000 meters")

            # Validate dimensionality
            if self.value.dimensionality != ureg.meter.dimensionality:
                raise ValidationError("Invalid unit dimensionality")

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

#### Unit Conversion Patterns

Standardize unit conversion approaches:

```python
from typing import Dict, Any
from decimal import Decimal


class ConversionMixin:
    """Mixin for common conversion patterns"""

    def to_unit(self, unit: str, round_digits: int = 2) -> ureg.Quantity:
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

        return {unit: self.to_unit(unit) for unit in self.get_valid_units()}

    def format_value(self, unit: Optional[str] = None, decimal_places: int = 2) -> str:
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
from typing import Optional


class MeasurementError(Exception):
    """Base exception for measurement errors"""

    pass


class UnitConversionError(MeasurementError):
    """Error for unit conversion issues"""

    pass


class MeasurementHandler:
    """Handler for safe measurement operations"""

    @staticmethod
    def safe_convert(value: ureg.Quantity, target_unit: str) -> Optional[ureg.Quantity]:
        """Safely convert between units"""
        try:
            return value.to(target_unit)
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
    value = DecimalPintField("meter", max_digits=10, decimal_places=2)

    def convert_value(self, target_unit: str) -> Optional[ureg.Quantity]:
        """Safely convert measurement value"""
        if self.value is None:
            return None

        try:
            return MeasurementHandler.safe_convert(self.value, target_unit)
        except UnitConversionError as e:
            logger.error(f"Conversion error: {e}")
            return None
```

### 3.3 Troubleshooting

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
            [str(value.units)],
        )
        return True
    except ValidationError:
        return False


### Usage
measurement = Measurement(value=ureg.Quantity("100 gram"))
is_compatible = validate_unit_compatibility(
    measurement.value, "meter"
)  # False - incompatible units
```

You can also use `check_matching_unit_dimension` directly.

2. Precision Loss:

Unlike `float` values, with `Decimal` values we do not use Python's `round` function. Instead, we should [quantize](https://docs.python.org/3/library/decimal.html#decimal.Decimal.quantize) the value, which more appropriately truncates (and optionally [rounds](https://docs.python.org/3/library/decimal.html#rounding-modes)) the Decimal value.

```python
from decimal import Decimal, ROUND_HALF_UP


def preserve_precision(value: ureg.Quantity, decimal_places: int = 2) -> ureg.Quantity:
    """Preserve decimal precision"""
    if value is None:
        return None

    magnitude = Decimal(str(value.magnitude))
    rounded = magnitude.quantize(
        Decimal(f"0.{'0' * decimal_places}"), rounding=ROUND_HALF_UP
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
        decimal_places=2,
    )

    def debug_info(self) -> dict:
        """Get detailed debug information"""
        if self.value is None:
            return {"error": "No value set"}

        return {
            "magnitude": self.value.magnitude,
            "units": str(self.value.units),
            "dimensionality": str(self.value.dimensionality),
            "base_value": self.value.to_base_units(),
            "valid_units": self.get_valid_units(),
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
        value__gt=ureg.Quantity("10 meter"),
    )
```

3. Validation Testing:

```python
from django.test import TestCase


class MeasurementTests(TestCase):
    def test_unit_conversion(self):
        """Test unit conversion accuracy"""
        measurement = Measurement.objects.create(
            value=ureg.Quantity("1000 meter"),
        )

        # Test conversion to kilometers
        km_value = measurement.value.to("kilometer")
        self.assertEqual(km_value.magnitude, 1)

        # Test conversion to miles
        mile_value = measurement.value.to("mile")
        self.assertAlmostEqual(mile_value.magnitude, 0.621371, places=6)
```

### 3.4 Edge Cases

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
        decimal_places=15,
    )

    def format_scientific(self, decimal_places: int = 2) -> str:
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

    value = DecimalPintField("meter", max_digits=10, decimal_places=2,)

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

## 4. Migration and Deployment

### 4.1 Database Considerations

When working with Django Pint Field in production environments, there are several important database considerations to keep in mind.

#### PostgreSQL Requirements

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "your_database",
        "USER": "your_user",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
        # Required settings for django-pint-field
        "OPTIONS": {
            "client_encoding": "UTF8",
        },
    }
}

# Ensure pint_field composite type is available
INSTALLED_APPS = [
    # ...
    "django_pint_field",
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
        ("your_app", "0001_initial"),
    ]

    def migrate_units_forward(apps, schema_editor):
        """Convert values to new units"""
        YourModel = apps.get_model("your_app", "YourModel")
        for instance in YourModel.objects.all():
            if instance.measurement is not None:
                # Convert to new unit
                instance.measurement = instance.measurement.to("new_unit")
                instance.save()

    def migrate_units_backward(apps, schema_editor):
        """Revert to original units"""
        YourModel = apps.get_model("your_app", "YourModel")
        for instance in YourModel.objects.all():
            if instance.measurement is not None:
                # Convert back to original unit
                instance.measurement = instance.measurement.to("original_unit")
                instance.save()

    operations = [
        migrations.RunPython(migrate_units_forward, migrate_units_backward),
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

    help = "Backup and restore PintField data"

    def serialize_quantity(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize Quantity objects for backup"""
        for field, value in obj.items():
            if hasattr(value, "magnitude") and hasattr(value, "units"):
                obj[field] = {
                    "magnitude": str(value.magnitude),
                    "units": str(value.units),
                    "comparator": str(value.to_base_units().magnitude),
                }
        return obj

    def deserialize_quantity(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize Quantity objects from backup"""
        for field, value in obj.items():
            if isinstance(value, dict) and all(
                k in value for k in ["magnitude", "units"]
            ):
                obj[field] = {
                    "magnitude": Decimal(value["magnitude"]),
                    "units": value["units"],
                    "comparator": Decimal(value["comparator"]),
                }
        return obj

    def backup_data(self, model, file_path: str) -> None:
        """Backup model data with PintFields"""
        with open(file_path, "w") as f:
            objects = model.objects.all()
            serialized_objects = [
                self.serialize_quantity(obj.__dict__) for obj in objects
            ]
            json.dump(serialized_objects, f, indent=2)

    def restore_data(self, model, file_path: str) -> None:
        """Restore model data with PintFields"""
        with open(file_path, "r") as f:
            objects = json.load(f)
            for obj_data in objects:
                deserialized_data = self.deserialize_quantity(obj_data)
                model.objects.create(**deserialized_data)
```

### 4.2 Production Setup

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

            logger.info("Unit conversion took %.3f seconds", duration)
            return result

        return wrapper

    @staticmethod
    def get_field_statistics(model) -> Dict[str, Any]:
        """Get statistics for PintField usage"""
        stats = {
            "total_records": model.objects.count(),
            "null_values": model.objects.filter(value__isnull=True).count(),
            "unique_units": model.objects.values("value__units").distinct().count(),
        }

        # Get unit distribution
        unit_distribution = model.objects.values("value__units").annotate(
            count=Count("id")
        )

        stats["unit_distribution"] = {
            item["value__units"]: item["count"] for item in unit_distribution
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
        category="pint_field",
        message=f"PintField operation: {operation}",
        data=data,
        level="info",
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
