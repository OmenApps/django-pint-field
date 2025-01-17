# Cookbook

```{caution}
This page is still under development, and may not reflect recent changes.
```

- [Cookbook](#cookbook)
  - [1. Practical Examples](#1-practical-examples)
    - [1.1 Unit Conversions](#11-unit-conversions)
      - [Automatic Conversion](#automatic-conversion)
      - [Manual Conversion](#manual-conversion)
      - [Base Unit Handling](#base-unit-handling)
    - [1.2 Custom Units](#12-custom-units)
      - [Creating Custom Unit Definitions](#creating-custom-unit-definitions)
      - [Registering Custom Units](#registering-custom-units)
      - [Usage in Models](#usage-in-models)
    - [1.3 Decimal Handling](#13-decimal-handling)
      - [Precision Management](#precision-management)
      - [Rounding Strategies](#rounding-strategies)
      - [Decimal Context Configuration](#decimal-context-configuration)
    - [1.4 Complex Unit Operations](#14-complex-unit-operations)
      - [Handling Derived Units](#handling-derived-units)
      - [Unit Dimensionality Validation](#unit-dimensionality-validation)
      - [Converting Between Unit Systems](#converting-between-unit-systems)
  - [2. Advanced Admin Actions](#2-advanced-admin-actions)
    - [2.1 Bulk Unit Conversion](#21-bulk-unit-conversion)
    - [2.2 Exporting Data with Specific Units](#22-exporting-data-with-specific-units)
    - [2.3 Mass Updates](#23-mass-updates)
  - [3. Serializer Customization](#3-serializer-customization)
    - [3.1 Custom Field Handling](#31-custom-field-handling)
    - [3.2 Unit Conversion in Serializers](#32-unit-conversion-in-serializers)
  - [4. Performance Optimization](#4-performance-optimization)
    - [4.1 Query Optimization](#41-query-optimization)
    - [4.2 Bulk Operations](#42-bulk-operations)
    - [4.3 Caching Strategies](#43-caching-strategies)
  - [5. Common Patterns](#5-common-patterns)
    - [5.1 Validation Strategies](#51-validation-strategies)
    - [5.2 Unit Conversion Patterns](#52-unit-conversion-patterns)
    - [5.3 Error Handling](#53-error-handling)
  - [6. Troubleshooting](#6-troubleshooting)
    - [6.1 Common Issues](#61-common-issues)
    - [6.2 Debugging Strategies](#62-debugging-strategies)
  - [7. Edge Cases](#7-edge-cases)
    - [7.1 Handling Very Large/Small Quantities](#71-handling-very-largesmall-quantities)
    - [7.2 Zero and Negative Values](#72-zero-and-negative-values)
  - [8. Migration and Deployment](#8-migration-and-deployment)
    - [8.1 Database Considerations](#81-database-considerations)
      - [PostgreSQL Requirements](#postgresql-requirements)
    - [8.2 Production Setup](#82-production-setup)
      - [Monitoring Tips](#monitoring-tips)
    - [8.3 Backup Strategies](#83-backup-strategies)
  - [9. Field Properties](#9-field-properties)
    - [9.1 Available Unit Conversions with Decimal Precision](#91-available-unit-conversions-with-decimal-precision)
    - [9.2 Validation Behavior with Decimal Precision](#92-validation-behavior-with-decimal-precision)
    - [9.3 Performance Considerations with Decimal Handling](#93-performance-considerations-with-decimal-handling)
    - [9.4 Best Practices for Querying with Decimal Handling](#94-best-practices-for-querying-with-decimal-handling)
  - [10. Aggregation Examples](#10-aggregation-examples)
    - [10.1 Simple Aggregations with Decimal Precision](#101-simple-aggregations-with-decimal-precision)
    - [10.2 Combining Aggregates with Unit Conversion](#102-combining-aggregates-with-unit-conversion)
    - [10.3 Advanced Aggregation with Decimal Precision](#103-advanced-aggregation-with-decimal-precision)
    - [10.4 Best Practices for Aggregations](#104-best-practices-for-aggregations)
  - [11. Customization Examples](#11-customization-examples)
      - [Example Implementation with Custom Cleaning](#example-implementation-with-custom-cleaning)
    - [11.2 Template Customization](#112-template-customization)
      - [Example Form with Custom Styling for Tabled Widget](#example-form-with-custom-styling-for-tabled-widget)


## 1. Practical Examples

### 1.1 Unit Conversions

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
        display_decimal_places=2,
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
        display_decimal_places=2,
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

### 1.2 Custom Units

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

### 1.3 Decimal Handling

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

#### Rounding Strategies

Implement different rounding approaches based on your needs:

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

#### Decimal Context Configuration

Manage decimal context for precise calculations:

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

### 1.4 Complex Unit Operations

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

#### Unit Dimensionality Validation

Ensure unit compatibility through dimensionality checks:

```python
from django.core.exceptions import ValidationError
from django_pint_field.units import ureg
from django_pint_field.validation import validate_dimensionality


class AreaCalculation(models.Model):
    length = DecimalPintField(
        "meter",
        display_decimal_places=2,
        unit_choices=["meter", "foot", "yard"],
    )
    width = DecimalPintField(
        "meter",
        display_decimal_places=2,
        unit_choices=["meter", "foot", "yard"],
    )
    area = DecimalPintField(
        "meter**2",
        display_decimal_places=2,
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

## 2. Advanced Admin Actions

### 2.1 Bulk Unit Conversion

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

### 2.2 Exporting Data with Specific Units

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

### 2.3 Mass Updates

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
        display_decimal_places=2,
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

## 3. Serializer Customization

### 3.1 Custom Field Handling

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

### 3.2 Unit Conversion in Serializers

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

## 4. Performance Optimization

### 4.1 Query Optimization

Implement efficient querying patterns to minimize database load:

```python
from django.db.models import F, Q, Prefetch
from django_pint_field.units import ureg
from django_pint_field.models import DecimalPintField
from django_pint_field.indexes import PintFieldComparatorIndex


class Measurement(models.Model):
    value = DecimalPintField(
        "meter",
        display_decimal_places=2,
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

### 4.2 Bulk Operations

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

### 4.3 Caching Strategies

Implement caching strategies to improve performance:

```python
from django.core.cache import cache
from django.db import models
from django_pint_field.models import DecimalPintField
from typing import Optional


class CachedMeasurement(models.Model):
    value = DecimalPintField(
        "meter",
        display_decimal_places=2,
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

## 5. Common Patterns

### 5.1 Validation Strategies

Implement robust validation patterns:

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

### 5.2 Unit Conversion Patterns

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

### 5.3 Error Handling

Implement consistent error handling patterns:

```python
from django.core.exceptions import ValidationError
from typing import Optional


class MeasurementError(Exception):
    """Base exception for measurement errors"""


class UnitConversionError(MeasurementError):
    """Error for unit conversion issues"""


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
    value = DecimalPintField("meter", display_decimal_places=2)

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

## 6. Troubleshooting

A great first place to look when experiencing issues with conversions, units, Quantity objects, etc is the [Pint documentation](https://pint.readthedocs.io/en/stable/).

### 6.1 Common Issues

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

### 6.2 Debugging Strategies

1. Value Inspection:

```python
class DebugMeasurement(models.Model):
    value = DecimalPintField(
        default_unit="meter",
        display_decimal_places=2,
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

## 7. Edge Cases

### 7.1 Handling Very Large/Small Quantities

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

### 7.2 Zero and Negative Values

```python
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
        """Get value sign"""
        if self.value is None:
            return None

        return 1 if self.value.magnitude > 0 else -1 if self.value.magnitude < 0 else 0
```

## 8. Migration and Deployment

### 8.1 Database Considerations

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

### 8.2 Production Setup

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

### 8.3 Backup Strategies

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

## 9. Field Properties

### 9.1 Available Unit Conversions with Decimal Precision

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
            unit: self.weight.to(unit).magnitude.quantize(
                Decimal(f"0.{'0' * precision}")
            )
            for unit in ["gram", "kilogram", "milligram", "pound", "ounce"]
        }


# Access built-in conversion properties with Decimal precision
measurement = WeightMeasurement.objects.first()
kg_value = measurement.weight__kilogram  # Returns Decimal value
gram_value = measurement.weight__gram  # Returns Decimal value
```

### 9.2 Validation Behavior with Decimal Precision

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

### 9.3 Performance Considerations with Decimal Handling

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

### 9.4 Best Practices for Querying with Decimal Handling

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

## 10. Aggregation Examples

### 10.1 Simple Aggregations with Decimal Precision

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

### 10.2 Combining Aggregates with Unit Conversion

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

### 10.3 Advanced Aggregation with Decimal Precision

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

### 10.4 Best Practices for Aggregations

```python
from django.db import models
from django_pint_field.aggregates import (
    PintAvg,
    PintCount,
    PintMax,
    PintMin,
    PintSum,
    PintStdDev,
    PintVariance,
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

## 11. Customization Examples

#### Example Implementation with Custom Cleaning

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

### 11.2 Template Customization

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

#### Example Form with Custom Styling for Tabled Widget

```python
from decimal import Decimal
from django_pint_field.forms import DecimalPintFormField
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

    class Media(DecimalPintFormField.Media):
        css = {"all": ["css/weight-form.css"]}
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
