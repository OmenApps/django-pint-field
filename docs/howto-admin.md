# Django Admin Integration

django-pint-field works with Django's admin interface out of the box. This guide covers registration, display customization, filtering, bulk actions, and data export.

## Registering Models with PintFields

Register models with PintFields the same way you would any other Django model:

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

PintFields are rendered in the admin with their default units automatically.

## Configuring List Display

You can display weights in multiple units by adding custom methods to your `ModelAdmin`:

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
            kg = obj.weight.kilogram
            return f"{kg.magnitude:.2f} {kg.units}"

    get_weight_kg.short_description = "Weight (kg)"

    def get_weight_lb(self, obj):
        """Display weight in pounds"""
        if obj.weight:
            lb = obj.weight.pound
            return f"{lb.magnitude:.2f} {lb.units}"

    get_weight_lb.short_description = "Weight (lb)"

    def get_weight_oz(self, obj):
        """Display weight in ounces"""
        if obj.weight:
            oz = obj.weight.ounce
            return f"{oz.magnitude:.1f} {oz.units}"

    get_weight_oz.short_description = "Weight (oz)"
```

### Using Property Shortcuts

django-pint-field provides a shorthand for unit conversion in `list_display` using double underscores. This avoids the need for custom methods in simple cases:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "weight",            # Original value
        "weight__kilogram",  # Converted to kg
        "weight__pound",     # Converted to lb
        "weight__ounce",     # Converted to oz
    ]

    list_display_links = ["name", "weight"]
```

## Advanced List Display

For more control over formatting, you can use `format_html` to add color coding or status indicators based on the weight magnitude:

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
        """Custom formatted weight display with color coding"""
        if not obj.weight:
            return "-"

        magnitude = obj.weight.gram.magnitude
        if magnitude >= 1000:
            value = obj.weight.kilogram
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
        """Display whether the item is above or below a threshold"""
        if not obj.weight:
            return "-"

        threshold = ureg.Quantity("500 gram")
        if obj.weight > threshold:
            text = "Heavy"
        else:
            text = "Light"

        return text

    weight_status.short_description = "Status"
```

## Custom Admin Forms

### Overriding Default Widgets

Replace the default widget with `TabledPintFieldWidget` to show a conversion table alongside the input:

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

### Adding Unit Conversion Displays

You can add a readonly field that shows the stored weight converted to several units at once:

```python
from django.utils.html import format_html, format_html_join


@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    readonly_fields = ["converted_weights"]

    def converted_weights(self, obj):
        if not obj or not obj.weight:
            return "-"

        qty = obj.weight.quantity
        conversions = {
            "gram": qty.to("gram"),
            "kilogram": qty.to("kilogram"),
            "pound": qty.to("pound"),
            "ounce": qty.to("ounce"),
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
    converted_weights.short_description = "Converted weights"
```

### Form Field Customization with Fieldsets

Combine custom widgets, extra fields, and fieldsets for a polished editing experience:

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

        self.fields["weight"].help_text = "Enter weight in any supported unit"
        self.fields["weight"].widget.attrs.update(
            {"class": "weight-input", "data-validation": "weight"}
        )

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

## Custom List Filters

Filter objects by weight range using a `SimpleListFilter`:

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

## Unit Conversion in List Display

Display the original weight alongside conversions, with optional CSS styling:

```python
@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight_with_conversions", "category"]
    list_filter = [WeightRangeFilter, "category"]

    def weight_with_conversions(self, obj):
        if not obj.weight:
            return "-"

        in_kg = obj.weight.kilogram
        in_lb = obj.weight.pound

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

Example CSS (`admin/css/weight_display.css`):

```css
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
```

## Search Functionality

Override `get_search_results` to let users search by weight values. This example matches objects within 10% of the searched quantity:

```python
from django.db.models import Q


@admin.register(WeightModel)
class WeightModelAdmin(admin.ModelAdmin):
    list_display = ["name", "weight", "category"]
    list_filter = [WeightRangeFilter, "category"]
    search_fields = ["name", "category__name"]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        # Try to parse the search term as a weight quantity
        try:
            search_quantity = ureg.Quantity(search_term)
            weight_q = Q(
                weight__gte=search_quantity.to("gram") * 0.9,
            ) & Q(
                weight__lte=search_quantity.to("gram") * 1.1,
            )
            queryset |= self.model.objects.filter(weight_q)
        except Exception:
            pass

        return queryset, use_distinct
```

## Bulk Unit Conversion

Admin actions can convert the stored unit for selected objects. The underlying `comparator` (used for cross-unit comparisons) stays the same; only the displayed magnitude and units change.

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
                obj.weight = obj.weight.quantity.to("kilogram")
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
                    obj.weight = obj.weight.quantity.to("pound")
                    obj.save()
                    updated += 1
            except Exception:
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
        """Convert weights to the most appropriate unit based on magnitude."""
        updated = 0

        for obj in queryset:
            if not obj.weight:
                continue

            weight_in_g = obj.weight.gram
            magnitude = weight_in_g.magnitude

            if magnitude >= 1_000_000:
                new_unit = "metric_ton"
            elif magnitude >= 1_000:
                new_unit = "kilogram"
            elif magnitude >= 1:
                new_unit = "gram"
            else:
                new_unit = "milligram"

            obj.weight = obj.weight.quantity.to(new_unit)
            obj.save()
            updated += 1

        self.message_user(
            request,
            f"Successfully standardized units for {updated} weights.",
            messages.SUCCESS,
        )
```

## Exporting Data with Specific Units

Export selected objects as CSV with the weight converted to multiple units in separate columns:

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

        header = field_names + ["weight_kg", "weight_lb", "weight_g"]
        writer.writerow(header)

        for obj in queryset:
            row_data = [getattr(obj, field) for field in field_names]

            if obj.weight:
                row_data.extend(
                    [
                        obj.weight.kilogram.magnitude,
                        obj.weight.pound.magnitude,
                        obj.weight.gram.magnitude,
                    ]
                )
            else:
                row_data.extend(["", "", ""])

            writer.writerow(row_data)

        return response
```

## Mass Updates

For more involved bulk operations, you can present an intermediate form that lets the admin user pick a target unit and an adjustment factor before applying changes.

```python
from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django_pint_field.units import ureg


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
                            converted = obj.weight.quantity.to(conversion_unit)
                            adjusted = converted.magnitude * adjustment_factor
                            obj.weight = ureg.Quantity(adjusted, conversion_unit)
                            obj.save()
                            updated += 1
                    except Exception:
                        errors += 1

                if updated:
                    self.message_user(
                        request,
                        f"Successfully updated {updated} weights.",
                        messages.SUCCESS,
                    )
                if errors:
                    self.message_user(
                        request,
                        f"Failed to update {errors} weights.",
                        messages.ERROR,
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

        return TemplateResponse(
            request, "admin/mass_weight_update.html", context
        )
```

Template for the intermediate page (`admin/mass_weight_update.html`):

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

## Range filters in the admin

`PintComparatorRangeListFilter` (from `django_pint_field.admin`) buckets a Pint
field into developer-defined ranges, compared cross-unit via the base-unit
comparator. Subclass it, set `parameter_name`, `title`, `field_name`, and
`ranges` (each `(label, low_quantity_or_None, high_quantity_or_None)`; bounds
are inclusive lower / exclusive upper):

```python
from django.contrib import admin

from django_pint_field.admin import PintComparatorRangeListFilter
from django_pint_field.units import ureg


class WeightBucketFilter(PintComparatorRangeListFilter):
    parameter_name = "weight_bucket"
    title = "weight"
    field_name = "weight"
    ranges = [
        ("under 1 kg", None, ureg.Quantity(1, "kilogram")),
        ("1-5 kg", ureg.Quantity(1, "kilogram"), ureg.Quantity(5, "kilogram")),
        ("5 kg and up", ureg.Quantity(5, "kilogram"), None),
    ]


class PackageAdmin(admin.ModelAdmin):
    list_filter = [WeightBucketFilter]
```

---

**See also:**

- [Forms, Widgets, and Templates](howto-forms-templates) for widget configuration details
