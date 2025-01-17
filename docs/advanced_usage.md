# Advanced Usage

```{caution}
This page is still under development, and may not reflect recent changes.
```

- [Advanced Usage](#advanced-usage)
  - [1.Django Admin Integration](#1django-admin-integration)
    - [1.1 Basic ModelAdmin Setup](#11-basic-modeladmin-setup)
      - [Registering Models with PintFields](#registering-models-with-pintfields)
      - [Default Admin Representation](#default-admin-representation)
      - [List Display Configuration](#list-display-configuration)
      - [Using Property Shortcuts](#using-property-shortcuts)
      - [Advanced List Display Configuration](#advanced-list-display-configuration)
    - [1.2 Custom Admin Forms](#12-custom-admin-forms)
      - [Custom Admin Forms Implementation](#custom-admin-forms-implementation)
        - [Overriding Default Widgets](#overriding-default-widgets)
        - [Manually Adding Unit Conversion Displays](#manually-adding-unit-conversion-displays)
        - [Form Field Customization](#form-field-customization)
    - [1.3 List Display and Filtering](#13-list-display-and-filtering)
      - [Custom List Filters](#custom-list-filters)
      - [Unit Conversion in List Display](#unit-conversion-in-list-display)
      - [Search Functionality](#search-functionality)
  - [2.REST Framework Integration](#2rest-framework-integration)
    - [2.1 Serializer Fields](#21-serializer-fields)
      - [String Format](#string-format)
      - [Dictionary Format](#dictionary-format)
    - [2.2 Serializer Examples](#22-serializer-examples)
      - [Basic Serializer Setup](#basic-serializer-setup)
      - [Using the Wrapped Representation](#using-the-wrapped-representation)
      - [Using Dictionary Format with PintRestField](#using-dictionary-format-with-pintrestfield)
      - [ViewSet Example](#viewset-example)
    - [2.3 Error Handling](#23-error-handling)
    - [2.4 Recommended Usage](#24-recommended-usage)
  - [3.Advanced Topics](#3advanced-topics)
    - [3.1 Composite Field Internals](#31-composite-field-internals)
      - [Field Structure](#field-structure)
      - [Storage Format](#storage-format)
      - [Performance Considerations](#performance-considerations)
    - [3.3 Database Optimization](#33-database-optimization)
      - [Index Strategies for Composite Fields](#index-strategies-for-composite-fields)
        - [Basic Django Indexes on the Field](#basic-django-indexes-on-the-field)
        - [Basic Django Indexes in the Model Meta Class](#basic-django-indexes-in-the-model-meta-class)
        - [Optimized Indexing with PintFieldComparatorIndex](#optimized-indexing-with-pintfieldcomparatorindex)
        - [Advanced PintFieldComparatorIndex Features](#advanced-pintfieldcomparatorindex-features)
        - [Performance Considerations for PintFieldComparatorIndex](#performance-considerations-for-pintfieldcomparatorindex)
      - [Bulk Operation Patterns](#bulk-operation-patterns)

## 1.Django Admin Integration

### 1.1 Basic ModelAdmin Setup

The django-pint-field package provides seamless integration with Django's admin interface. Here's how to set up and customize your admin for models with PintFields:

#### Registering Models with PintFields

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

#### Default Admin Representation

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

#### List Display Configuration

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

#### Using Property Shortcuts

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

#### Advanced List Display Configuration

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

### 1.2 Custom Admin Forms

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

##### Manually Adding Unit Conversion Displays

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

##### Form Field Customization

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

### 1.3 List Display and Filtering

#### Custom List Filters

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

#### Unit Conversion in List Display

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

#### Search Functionality

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


## 2.REST Framework Integration

Django Pint Field provides seamless integration with Django REST Framework (DRF) through specialized serializer fields. This integration allows you to serialize and deserialize Pint quantities in your API endpoints while maintaining unit consistency and proper validation.

### 2.1 Serializer Fields

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

### 2.2 Serializer Examples

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

### 2.3 Error Handling

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

### 2.4 Recommended Usage

1. Use `PintRestField` when:

   - You need a more structured, explicit format
   - Working with APIs where the data structure is more important than human readability
   - Dealing with front-end applications that expect consistent JSON structures

2. Use `IntegerPintRestField` / `DecimalPintRestField` when:
   - You need a more compact, human-readable format
   - Working with APIs where string representation is preferred
   - Dealing with systems that expect string-based representations

## 3.Advanced Topics

### 3.1 Composite Field Internals

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

1. The user-specified original value is preserved in the `magnitude` and `units` fields
2. The value is converted to "[base units](https://pint.readthedocs.io/en/stable/user/systems.html)" and stored in `comparator`
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
        display_decimal_places=2,
        db_index=True,  # This creates a basic index
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

### 3.3 Database Optimization

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
        display_decimal_places=2,
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
        display_decimal_places=2,
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
        display_decimal_places=2,
    )
    height = DecimalPintField(
        "meter",
        display_decimal_places=2,
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
        display_decimal_places=2,
    )
    volume = DecimalPintField(
        "liter",
        display_decimal_places=2,
    )
    temperature = DecimalPintField(
        "celsius",
        display_decimal_places=2,
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
# 2.Match index order in queries
measurements = OptimizedMeasurement.objects.filter(
    weight__gt=ureg.Quantity("100 gram"),
    height__gt=ureg.Quantity("1 meter"),
).order_by(
    "weight", "height"
)  # Matches index order defined in the index

# 3.Use covering indexes for frequently accessed fields
frequent_queries = AdvancedMeasurement.objects.filter(
    volume__gt=ureg.Quantity("2 liter")
).values(
    "id", "temperature"
)  # Uses covering index

# 4.Leverage partial indexes for filtered queries
positive_weights = AdvancedMeasurement.objects.filter(
    weight__gt=ureg.Quantity("0 gram")
).order_by(
    "weight"
)  # Uses partial index

# 5.Consider index size vs query performance.
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
