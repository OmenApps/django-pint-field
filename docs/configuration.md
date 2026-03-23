# Configuration

django-pint-field provides three settings that can be configured in your Django project's `settings.py`. All settings are optional and have sensible defaults.

## Settings Overview

| Setting                               | Type           | Default                                   | Description                                                                                                              |
| ------------------------------------- | -------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `DJANGO_PINT_FIELD_UNIT_REGISTER`     | `UnitRegistry` | `pint.UnitRegistry(non_int_type=Decimal)` | The Pint unit registry used throughout the project                                                                       |
| `DJANGO_PINT_FIELD_DECIMAL_PRECISION` | `int`          | `0`                                       | Project-wide decimal precision; if > 0, sets Python's decimal context precision                                          |
| `DJANGO_PINT_FIELD_DEFAULT_FORMAT`    | `str`          | `"D"`                                     | Default [Pint format string](https://pint.readthedocs.io/en/stable/user/formatting.html) for displaying Quantity objects |

## DJANGO_PINT_FIELD_UNIT_REGISTER

Controls which Pint `UnitRegistry` the package uses. The default registry is created with `non_int_type=Decimal`, so all numeric values use Python's `Decimal` type.

You typically override this setting when you need custom units:

```python
# settings.py
from pint import UnitRegistry
from decimal import Decimal

custom_ureg = UnitRegistry(non_int_type=Decimal)

# Define custom units
custom_ureg.define("serving = [serving]")
custom_ureg.define("scoop = 2 * serving")
custom_ureg.define("dozen = 12 * serving")

DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
```

All PintFields in the project share this registry. Once set, the custom units are available everywhere.

For more on defining units, see the [Pint documentation on custom units](https://pint.readthedocs.io/en/stable/advanced/defining.html).

## DJANGO_PINT_FIELD_DECIMAL_PRECISION

Sets the precision for Python's [decimal context](https://docs.python.org/3/library/decimal.html#mitigating-round-off-error-with-increased-precision). When set to a value greater than 0, the package calls `getcontext().prec = value` at startup.

```python
# settings.py

# Use Python's default precision (28 digits)
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 0

# Or set a higher precision for scientific applications
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 40
```

This affects all `Decimal` operations in the process, not just django-pint-field. Set it only if you need precision beyond the default 28 digits.

## DJANGO_PINT_FIELD_DEFAULT_FORMAT

Controls the default string representation of Quantity objects. This uses Pint's [format specification](https://pint.readthedocs.io/en/stable/user/formatting.html).

Common format strings:

| Format | Example Output | Description                          |
| ------ | -------------- | ------------------------------------ |
| `"D"`  | `500.00 gram`  | Default format                       |
| `"P"`  | `500.00 gram`  | Pretty format                        |
| `"~P"` | `500.00 g`     | Pretty format with abbreviated units |
| `"C"`  | `500.00 gram`  | Compact format                       |
| `"H"`  | `500.00 gram`  | HTML format                          |

```python
# settings.py
DJANGO_PINT_FIELD_DEFAULT_FORMAT = "~P"  # Use abbreviated units
```

## Complete Example

```python
# settings.py
from pint import UnitRegistry
from decimal import Decimal

# Create a custom registry with Decimal support
custom_ureg = UnitRegistry(non_int_type=Decimal)
custom_ureg.define("serving = [serving]")

# Configure django-pint-field
DJANGO_PINT_FIELD_UNIT_REGISTER = custom_ureg
DJANGO_PINT_FIELD_DECIMAL_PRECISION = 40
DJANGO_PINT_FIELD_DEFAULT_FORMAT = "D"
```
