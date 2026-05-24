# API Reference

This page documents all public classes, functions, and parameters in django-pint-field.

## Model Fields

### BasePintField

`django_pint_field.models.BasePintField`

Base class for all PintField types. You do not use this directly; use `IntegerPintField` or `DecimalPintField` instead.

**Parameters:**

| Parameter      | Type                      | Required | Default | Description                                                                                                               |
| -------------- | ------------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| `default_unit` | `str`, `tuple[str, str]`, or `list[str, str]` | Yes      | --      | The default unit for this field. Can be a string (`"gram"`) or a display/value pair (`["Gram", "gram"]`).                 |
| `unit_choices` | `list`                    | No       | `None`  | Available units for this field. Each item can be a string or a display/value pair. The `default_unit` is always included. |
| `null`         | `bool`                    | No       | `False` | Allow NULL in the database.                                                                                               |
| `blank`        | `bool`                    | No       | `False` | Allow blank values in forms.                                                                                              |
| `verbose_name` | `str`                     | No       | `None`  | Human-readable field name.                                                                                                |
| `help_text`    | `str`                     | No       | `""`    | Help text for forms.                                                                                                      |

**Key methods:**

- `db_type(connection)` -- Returns `"pint_field"` (the PostgreSQL composite type).
- `from_db_value(value, expression, connection)` -- Converts the database composite value into a `PintFieldProxy`.
- `get_prep_value(value)` -- Prepares a Python value for use in database queries.
- `to_python(value)` -- Converts any input value to a Pint `Quantity`.
- `validate(value, model_instance)` -- Runs field validation including dimensionality checks.
- `formfield(**kwargs)` -- Returns the appropriate form field for this model field.
- `value_to_string(obj)` -- Returns a string representation for serialization.

### IntegerPintField

`django_pint_field.models.IntegerPintField`

A PintField that stores the magnitude as an integer. Inherits all parameters from `BasePintField`.

Best for measurements where whole numbers are expected (counts, simple weights where decimal places are not needed). Internally, the value is stored as a decimal, but form input and display use integers.

Uses `IntegerPintFormField` as the default form field.

```python
from django_pint_field.models import IntegerPintField

class Product(models.Model):
    weight = IntegerPintField("gram", unit_choices=["gram", "kilogram"])
```

### DecimalPintField

`django_pint_field.models.DecimalPintField`

A PintField that stores the magnitude as a decimal. Inherits all parameters from `BasePintField`, plus:

| Parameter                | Type  | Required | Default | Description                                                                         |
| ------------------------ | ----- | -------- | ------- | ----------------------------------------------------------------------------------- |
| `display_decimal_places` | `int` | No       | `None`  | Number of decimal places to show in display and forms.                              |
| `rounding_method`        | `str` | No       | `None`  | Rounding method for decimal operations. Accepts any Python `decimal` rounding mode. |

Available rounding methods: `ROUND_CEILING`, `ROUND_DOWN`, `ROUND_FLOOR`, `ROUND_HALF_DOWN`, `ROUND_HALF_EVEN`, `ROUND_HALF_UP`, `ROUND_UP`, `ROUND_05UP`.

Uses `DecimalPintFormField` as the default form field.

```python
from django_pint_field.models import DecimalPintField

class Sample(models.Model):
    mass = DecimalPintField(
        "gram",
        display_decimal_places=4,
        rounding_method="ROUND_HALF_UP",
    )
```

## Field Descriptor and Proxy

### PintFieldDescriptor

`django_pint_field.models.PintFieldDescriptor`

A [descriptor](https://docs.python.org/3/howto/descriptor.html) that intercepts attribute access on PintField model attributes. When you access `instance.weight`, the descriptor returns a `PintFieldProxy` instead of a raw value. You do not interact with this class directly.

### PintFieldProxy

`django_pint_field.helpers.PintFieldProxy`

Wraps a Pint `Quantity` to add attribute-based unit conversion. Returned whenever you access a PintField value on a model instance.

**Attribute access patterns:**

| Access                        | Returns     | Example                                             |
| ----------------------------- | ----------- | --------------------------------------------------- |
| `proxy.magnitude`             | `Decimal`   | `Decimal('500.00')`                                 |
| `proxy.units`                 | `pint.Unit` | `gram`                                              |
| `proxy.quantity`              | `Quantity`  | The underlying Pint `Quantity` object               |
| `proxy.quantity.to(unit)`     | `Quantity`  | `proxy.quantity.to("kilogram")`                     |
| `proxy.<unit_name>`           | `Quantity`  | `proxy.kilogram` returns value in kilograms         |
| `proxy.<unit_name>__<digits>` | `Quantity`  | `proxy.kilogram__2` returns `0.50 kilogram`         |
| `proxy.digits__<N>`           | `Quantity`  | `proxy.digits__2` returns value rounded to 2 places |

**Supported operators:**

Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
Arithmetic: `+`, `-`, `*`, `/`, `//`, `%`

All comparisons and arithmetic operations are unit-aware and raise errors on incompatible dimensions.

### PintFieldMixin

`django_pint_field.models.PintFieldMixin`

A mixin added to all PintField types. Adds dynamic unit conversion properties to the model class at creation time.

**Key methods:**

- `add_properties(cls, name)` -- Called during model class creation. For a field named `weight`, adds `weight__<unit>` properties for compatible units available in the active registry.
- `contribute_to_class(cls, name, **kwargs)` -- Standard Django field hook. Installs the `PintFieldDescriptor` and calls `add_properties`.

## Form Fields

### IntegerPintFormField

`django_pint_field.forms.IntegerPintFormField`

Form field for `IntegerPintField` models.

| Parameter      | Type            | Required | Default    | Description                    |
| -------------- | --------------- | -------- | ---------- | ------------------------------ |
| `default_unit` | `str` or `list` | Yes      | --         | Default unit for the field.    |
| `unit_choices` | `list`          | No       | `None`     | Available unit choices.        |
| `min_value`    | `int`           | No       | `-2^63`    | Minimum allowed value.         |
| `max_value`    | `int`           | No       | `2^63 - 1` | Maximum allowed value.         |
| `required`     | `bool`          | No       | `True`     | Whether the field is required. |

### DecimalPintFormField

`django_pint_field.forms.DecimalPintFormField`

Form field for `DecimalPintField` models.

| Parameter                | Type            | Required | Default           | Description                    |
| ------------------------ | --------------- | -------- | ----------------- | ------------------------------ |
| `default_unit`           | `str` or `list` | Yes      | --                | Default unit for the field.    |
| `unit_choices`           | `list`          | No       | `None`            | Available unit choices.        |
| `display_decimal_places` | `int`           | No       | `None`            | Decimal places to display.     |
| `rounding_method`        | `str`           | No       | `"ROUND_HALF_UP"` | Rounding method for display.   |
| `required`               | `bool`          | No       | `True`            | Whether the field is required. |

## Widgets

### PintFieldWidget

`django_pint_field.widgets.PintFieldWidget`

The default widget for PintFields. Renders a numeric input alongside a unit selection dropdown.

| Parameter      | Type            | Required | Default           | Description                              |
| -------------- | --------------- | -------- | ----------------- | ---------------------------------------- |
| `default_unit` | `str` or `list` | Yes      | --                | Default unit for the widget.             |
| `unit_choices` | `list`          | No       | `None`            | Available unit choices for the dropdown. |
| `attrs`        | `dict`          | No       | `{"step": "any"}` | HTML attributes for the numeric input.   |

### TabledPintFieldWidget

`django_pint_field.widgets.TabledPintFieldWidget`

Extends `PintFieldWidget` by adding a table that shows the current value converted to all available units.

Inherits all parameters from `PintFieldWidget`, plus:

| Parameter              | Type   | Default | Description                                         |
| ---------------------- | ------ | ------- | --------------------------------------------------- |
| `floatformat`          | `int`  | `-1`    | Number of decimal places in the conversion table.   |
| `table_class`          | `str`  | `""`    | CSS class for the `<table>` element.                |
| `thead_class`          | `str`  | `""`    | CSS class for the `<thead>` element.                |
| `tbody_class`          | `str`  | `""`    | CSS class for the `<tbody>` element.                |
| `tr_header_class`      | `str`  | `""`    | CSS class for header `<tr>` elements.               |
| `tr_class`             | `str`  | `""`    | CSS class for body `<tr>` elements.                 |
| `th_class`             | `str`  | `""`    | CSS class for `<th>` elements.                      |
| `td_class`             | `str`  | `""`    | CSS class for `<td>` elements.                      |
| `td_unit_class`        | `str`  | `""`    | CSS class for unit name cells.                      |
| `td_value_class`       | `str`  | `""`    | CSS class for value cells.                          |
| `input_wrapper_class`  | `str`  | `""`    | CSS class for the wrapper around the input section. |
| `table_wrapper_class`  | `str`  | `""`    | CSS class for the wrapper around the table section. |
| `unit_header`          | `str`  | `None`  | Custom header text for the units column.            |
| `value_header`         | `str`  | `None`  | Custom header text for the values column.           |
| `show_units_in_values` | `bool` | `False` | Whether to display units in value cells.            |

The widget template can be overridden at: `templates/django_pint_field/tabled_django_pint_field_widget.html`

## Serializer Fields (Django REST Framework)

### IntegerPintRestField

`django_pint_field.rest.IntegerPintRestField`

String-based serialization for `IntegerPintField`.

| Parameter | Type   | Default | Description                                                                        |
| --------- | ------ | ------- | ---------------------------------------------------------------------------------- |
| `wrap`    | `bool` | `False` | If `True`, output is `"Quantity(1000 gram)"`. If `False`, output is `"1000 gram"`. |

Accepts string input like `"1000 gram"` or `"Quantity(1000 gram)"`.

### DecimalPintRestField

`django_pint_field.rest.DecimalPintRestField`

String-based serialization for `DecimalPintField`.

| Parameter | Type   | Default | Description                                                                      |
| --------- | ------ | ------- | -------------------------------------------------------------------------------- |
| `wrap`    | `bool` | `False` | If `True`, output is `"Quantity(1.5 gram)"`. If `False`, output is `"1.5 gram"`. |

Accepts string input like `"1.5 gram"` or `"Quantity(1.5 gram)"`.

### PintRestField

`django_pint_field.rest.PintRestField`

Dictionary-based serialization for any PintField.

Output format:

```json
{ "magnitude": 1.5, "units": "gram" }
```

Accepts dictionary input with `magnitude` and `units` keys.

## Aggregates

`django_pint_field.aggregates`

All aggregates accept a field name as the first argument and return results with proper unit handling.

| Aggregate                           | Returns          | Description                                                          |
| ----------------------------------- | ---------------- | -------------------------------------------------------------------- |
| `PintCount(field)`                  | `int`            | Count of non-null values.                                            |
| `PintAvg(field)`                    | `PintFieldProxy` | Average value.                                                       |
| `PintSum(field)`                    | `PintFieldProxy` | Sum of values.                                                       |
| `PintMax(field)`                    | `PintFieldProxy` | Maximum value.                                                       |
| `PintMin(field)`                    | `PintFieldProxy` | Minimum value.                                                       |
| `PintStdDev(field, sample=False)`   | `PintFieldProxy` | Standard deviation. Set `sample=True` for sample standard deviation. |
| `PintVariance(field, sample=False)` | `PintFieldProxy` | Variance. Set `sample=True` for sample variance.                     |
| `PintPercentile(field, percentile)` | `PintFieldProxy` | Continuous percentile (`percentile` in [0, 1]) via `PERCENTILE_CONT`. |
| `PintMedian(field)`                 | `PintFieldProxy` | Median (50th percentile).                                            |

Aggregates that return a `PintFieldProxy` accept an optional `output_unit=` to convert the result. The `pint_histogram(queryset, field_name, *, buckets, min_value, max_value)` helper returns a list of `{"bucket", "lower", "upper", "count"}` dicts (boundaries as `Quantity`, in base units) computed with PostgreSQL `width_bucket`.

```python
from django_pint_field.aggregates import PintAvg, PintSum

Product.objects.aggregate(
    avg_weight=PintAvg("weight"),
    total_weight=PintSum("weight"),
)
```

## Expressions

`django_pint_field.expressions`

SQL-native query expressions that read and transform the `pint_field` composite directly in PostgreSQL.

| Expression                     | Returns        | Description                                                                          |
| ------------------------------ | -------------- | ------------------------------------------------------------------------------------ |
| `PintComparator(field)`        | `DecimalField` | The base-unit `comparator` component.                                                |
| `PintMagnitude(field)`         | `DecimalField` | The originally stored `magnitude` component.                                         |
| `PintConvert(field, to_unit)`  | `DecimalField` | The magnitude converted to `to_unit`, computed in SQL (handles offset units).        |

```python
from django_pint_field import PintConvert

Product.objects.annotate(kg=PintConvert("weight", "kilogram")).filter(kg__gte=2)
```

`PintConvert` raises `ValueError` for an empty `to_unit` and `pint.UndefinedUnitError` for an unknown one, both at expression construction. It does not validate dimensional compatibility - see [Querying](howto-queries) for the indexing and precision caveats.

## Lookups

PintFields support the following lookups. All comparisons operate on the `comparator` component (the base-unit magnitude), so they work correctly across different units.

**Supported lookups:**

| Lookup   | Example                                                       |
| -------- | ------------------------------------------------------------- |
| `exact`  | `filter(weight=quantity)` or `filter(weight__exact=quantity)` |
| `gt`     | `filter(weight__gt=quantity)`                                 |
| `gte`    | `filter(weight__gte=quantity)`                                |
| `lt`     | `filter(weight__lt=quantity)`                                 |
| `lte`    | `filter(weight__lte=quantity)`                                |
| `range`  | `filter(weight__range=(min_qty, max_qty))`                    |
| `isnull` | `filter(weight__isnull=True)`                                 |

**Unsupported lookups** (raise `PintFieldLookupError`):

`contains`, `icontains`, `in`, `startswith`, `istartswith`, `endswith`, `iendswith`, `date`, `year`, `iso_year`, `month`, `day`, `week`, `iso_week_day`, `week_day`, `quarter`, `time`, `hour`, `minute`, `second`, `regex`, `iregex`, `search`, `isearch`

These lookups are disabled because PintFields store composite types, not simple text or date values.

## Indexes

### PintFieldComparatorIndex

`django_pint_field.indexes.PintFieldComparatorIndex`

A specialized index that targets the `comparator` component of PintField columns. This provides better query performance than a standard index on the full composite field.

| Parameter       | Type        | Required | Default        | Description                                     |
| --------------- | ----------- | -------- | -------------- | ----------------------------------------------- |
| `fields`        | `list[str]` | Yes      | --             | Field names to index.                           |
| `name`          | `str`       | No       | auto-generated | Index name.                                     |
| `condition`     | `Q`         | No       | `None`         | Django `Q` object for a partial index.          |
| `include`       | `list[str]` | No       | `None`         | Additional columns to include (covering index). |
| `db_tablespace` | `str`       | No       | `None`         | PostgreSQL tablespace for the index.            |
| `opclasses`     | `list[str]` | No       | `()`           | Operator classes for the index.                 |

```python
from django_pint_field.indexes import PintFieldComparatorIndex

class Product(models.Model):
    weight = DecimalPintField("gram")

    class Meta:
        indexes = [
            PintFieldComparatorIndex(fields=["weight"]),
        ]
```

## Adapters

### PintDumper

`django_pint_field.adapters.PintDumper`

A psycopg3 `Dumper` subclass that serializes Pint `Quantity` objects into the PostgreSQL composite type format. This is registered automatically when django-pint-field initializes; you should not need to interact with it directly.

## Exceptions

### PintFieldLookupError

`django_pint_field.exceptions.PintFieldLookupError`

Subclass of Django's `FieldError`. Raised when an unsupported lookup is used on a PintField.

```python
# This raises PintFieldLookupError:
Product.objects.filter(weight__contains="gram")
```

## Units

### ureg

`django_pint_field.units.ureg`

The global `UnitRegistry` instance used by all PintFields. By default, this is a `pint.UnitRegistry(non_int_type=Decimal)`.

If you set `DJANGO_PINT_FIELD_UNIT_REGISTER` in your settings, `ureg` points to your custom registry instead.

```python
from django_pint_field.units import ureg

quantity = ureg.Quantity("500 gram")
```

## Validation

### QuantityConverter

`django_pint_field.validation.QuantityConverter`

Handles conversion of various input types to Pint `Quantity` objects.

| Parameter       | Type           | Default     | Description                                     |
| --------------- | -------------- | ----------- | ----------------------------------------------- |
| `default_unit`  | `str`          | --          | Default unit for conversions.                   |
| `field_type`    | `str`          | `"decimal"` | `"decimal"` or `"integer"`.                     |
| `unit_registry` | `UnitRegistry` | `None`      | Custom registry; if omitted, `QuantityConverter` creates a new `UnitRegistry()`. |

**Method:**

- `convert(value)` -- Converts the input to a `Quantity`. Accepts: `str`, `int`, `float`, `Decimal`, `Quantity`, `list`/`tuple`, `dict`, or `PintFieldProxy`.

### Validator Functions

| Function                                            | Description                                                                                               |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `validate_unit_choices(unit_choices, default_unit)` | Validates and normalizes unit choices. Returns `list[tuple[str, str]]`.                                   |
| `validate_dimensionality(value, default_unit)`      | Checks that a value's unit dimensionality matches the default unit. Raises `ValidationError` on mismatch. |
| `validate_required_value(value, required, blank)`   | Validates that a required field has a non-empty value.                                                    |
| `validate_decimal_precision(value, allow_rounding)` | Validates that a decimal value does not exceed the context precision.                                     |
| `validate_value_range(value, min_value, max_value)` | Validates that a value falls within the specified range, with unit-aware comparison.                      |

## Typing and Performance

django-pint-field ships a `py.typed` marker (PEP 561), so type checkers and IDEs recognize its public API as typed.

Each `PintField` instance reuses a single `PintFieldConverter` (via `get_cached_converter()`), so loading N rows allocates one converter rather than one per row. This is an internal optimization and does not change any returned values.

For a model instance loaded from the database, the field value is wrapped once in a `PintFieldProxy` and stored on the instance, so repeated reads return the same object. Attribute-based unit access (e.g. `obj.weight.kilogram`) is available on loaded instances.
