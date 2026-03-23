# Forms, Widgets, and Templates

This guide covers how to build forms with PintFields, configure the built-in widgets, customize their appearance, and display quantity values in templates.

## Using PintFields in Forms

django-pint-field ships with two form field types that correspond to the model fields. Both support unit selection dropdowns and value validation out of the box.

### IntegerPintFormField

Use `IntegerPintFormField` for whole-number quantities. It pairs with `IntegerPintField` on the model side.

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

The `unit_choices` parameter controls which units appear in the dropdown. Each entry can be a plain string (`"gram"`) or a two-element tuple with a display label and the unit string (`("Gram", "gram")`).

### DecimalPintFormField

Use `DecimalPintFormField` for precise measurements that need decimal places. It pairs with `DecimalPintField` on the model side.

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

The `display_decimal_places` parameter controls how many decimal digits are shown. The `rounding_method` accepts any Python `decimal` module rounding constant as a string, such as `"ROUND_HALF_UP"`, `"ROUND_CEILING"`, or `"ROUND_DOWN"`.

## Configuring the Default Widget

`PintFieldWidget` is the default widget for all PintFields. It renders a numeric input alongside a unit selection dropdown. You can customize it in a `ModelForm` by overriding the `widgets` dictionary in `Meta`.

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
                attrs={"step": "0.01"},
            )
        }
```

The `attrs` dictionary passes HTML attributes directly to the numeric input element. Setting `step` to `"0.01"` allows two-decimal-place input in browsers that enforce step validation.

## Using the Tabled Widget

`TabledPintFieldWidget` extends the default widget by adding a conversion table below the input. When a user enters a value, the table displays that value converted to every unit in `unit_choices`.

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
                table_class="conversion-table",  # CSS class for the <table>
                td_class="text-end",  # CSS class for <td> elements
                show_units_in_values=True,  # Show unit labels in value cells
            )
        }
```

Configuration options at a glance:

- `floatformat` -- number of decimal places shown in the conversion table cells
- `table_class` -- CSS class applied to the `<table>` element
- `td_class` -- CSS class applied to each `<td>` element
- `show_units_in_values` -- when `True`, the unit name appears next to each converted value

## Customizing Widget Styling

For richer styling, configure the tabled widget with CSS framework classes (Bootstrap, Tailwind, etc.) and add custom CSS for fine-grained control.

```python
from decimal import Decimal
from django_pint_field.forms import DecimalPintFormField
from django_pint_field.widgets import TabledPintFieldWidget


class WeightForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["weight"].widget = TabledPintFieldWidget(
            default_unit="gram",
            unit_choices=[
                ("Gram", "gram"),
                ("Kilogram", "kilogram"),
                ("Pound", "pound"),
            ],
            floatformat=2,
            table_class="table table-striped table-hover",
            td_class="text-end",
            show_units_in_values=True,
            attrs={
                "step": "0.01",
            },
        )

    class Meta:
        model = Product
        fields = ["name", "weight"]

    class Media:
        css = {"all": ["css/weight-form.css"]}
```

A companion CSS file for the conversion table:

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

## Implementing Custom Form Cleaning

Override `clean_<fieldname>()` to add validation logic that goes beyond simple min/max bounds. The cleaned value is a Pint `Quantity` object, so you can compare it against other quantities directly, even across different units.

```python
from decimal import Decimal
from django import forms
from django_pint_field.widgets import PintFieldWidget
from django_pint_field.units import ureg


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["weight"].widget = PintFieldWidget(
            default_unit="gram",
            unit_choices=[
                ("Gram", "gram"),
                ("Kilogram", "kilogram"),
                ("Pound", "pound"),
            ],
            attrs={
                "class": "weight-input",
                "step": "0.01",
                "data-toggle": "tooltip",
                "title": "Enter product weight",
            },
        )

    def clean_weight(self):
        """Custom validation for weight field with decimal precision."""
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

Because `Quantity` objects handle unit conversion automatically, comparing a value in grams against a limit in kilograms works without any manual conversion.

## Customizing the Widget Template

The tabled widget renders through a Django template that you can override in your project. Place your custom version at:

```
templates/django_pint_field/tabled_django_pint_field_widget.html
```

Here is an example custom template:

```html
{% spaceless %}
<div class="pint-field-inputs">
  {% for widget in widget.subwidgets %} {% include widget.template_name %} {%
  endfor %}
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
          {{ value_item.magnitude|floatformat:floatformat }} {% if
          show_units_in_values %} {{ value_item.units }} {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endif %} {% endspaceless %}
```

The template context provides:

- `widget.subwidgets` -- the numeric input and unit dropdown
- `values_list` -- a list of converted values, each with `.magnitude` and `.units`
- `table_class`, `td_class`, `floatformat`, `show_units_in_values` -- the options passed to the widget constructor

## Displaying PintField Values in Templates

PintField values are accessible in templates just like any other model attribute. The value exposes `.magnitude` and `.units` for granular control.

```html
<!-- Full quantity string (e.g., "500.00 gram") -->
{{ product.weight }}

<!-- Magnitude only (e.g., "500.00") -->
{{ product.weight.magnitude }}

<!-- Units only (e.g., "gram") -->
{{ product.weight.units }}
```

You can also use the proxy's unit conversion properties directly in templates:

```html
<!-- Convert to kilograms -->
{{ product.weight.kilogram }}

<!-- Convert to pounds -->
{{ product.weight.pound }}
```

See the [Cheatsheet](cheatsheet) for comprehensive template filter examples and formatting patterns.

---

**Related pages:**

- [API Reference](reference) -- complete list of widget and form field parameters
- [Cheatsheet](cheatsheet) -- template filter examples and syntax quick reference
