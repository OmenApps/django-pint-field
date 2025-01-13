"""Form fields for the Django Pint Field package."""

import copy
import logging
import warnings
from collections.abc import Iterable  # pylint: disable=E0611
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import Optional

from django import forms
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .helpers import get_quantizing_string
from .units import ureg
from .validation import QuantityConverter
from .validation import validate_decimal_precision
from .validation import validate_dimensionality
from .validation import validate_required_value
from .validation import validate_unit_choices
from .validation import validate_value_range
from .widgets import PintFieldWidget


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity


def is_special_admin_widget(widget) -> bool:
    """Check if the widget is a special admin widget that should be ignored."""
    widgets_to_ignore = [
        FORMFIELD_FOR_DBFIELD_DEFAULTS[models.IntegerField],
        FORMFIELD_FOR_DBFIELD_DEFAULTS[models.BigIntegerField],
    ]
    classes_to_ignore = [ignored_widget["widget"].__name__ for ignored_widget in widgets_to_ignore]

    widget_class_name = getattr(widget, "__name__", None) or getattr(widget, "__class__").__name__
    return widget_class_name in classes_to_ignore


class BasePintFormField(forms.Field):
    """Base form field to choose which unit to use to enter a value which is saved to the composite field.

    Some of the __init__() logic is copied from the django.forms.fields.Field class, because simply calling
    `super().__init__(*args, **kwargs)` would overwrite the widget attribute.
    """

    widget = PintFieldWidget
    template_name = "django/forms/widgets/input.html"

    def __init__(  # pylint: disable=W0231
        self,
        *,
        default_unit: str | tuple[str, str] | list[str, str],
        unit_choices: Optional[Iterable[str] | Iterable[Iterable[str]]] = None,
        required: bool = True,
        widget=None,
        label: str = None,
        initial: Any = None,
        help_text: str = "",
        error_messages=None,
        show_hidden_initial: bool = False,
        validators=(),
        localize: bool = False,
        disabled: bool = False,
        label_suffix: str = None,
    ):
        """Initialize the Pint form field."""

        if default_unit is None:
            raise ValidationError("PintFormField requires a default_unit kwarg of a single unit type (eg: 'grams')")
        # Normalize default_unit to tuple format
        if isinstance(default_unit, str):
            self._default_unit_display = default_unit
            self._default_unit_value = default_unit
        elif isinstance(default_unit, (list, tuple)) and len(default_unit) == 2:
            self._default_unit_display, self._default_unit_value = default_unit
        else:
            raise ValidationError(
                "default_unit must be either a string or a 2-tuple/2-list of (display_name, unit_value)"
            )
        self.default_unit = self._default_unit_value
        self.ureg = ureg

        self.required = required
        self.label = label
        self.initial = initial
        self.show_hidden_initial = show_hidden_initial
        self.help_text = help_text
        self.disabled = disabled
        self.label_suffix = label_suffix
        self.localize = localize

        self.min_value = None
        self.max_value = None

        # Normalize unit choices using the same validation function as the model field
        self.unit_choices = validate_unit_choices(unit_choices, default_unit)
        if not any(value == default_unit for _, value in self.unit_choices):
            self.unit_choices.insert(0, (default_unit, default_unit))

        widget = self._setup_widget(widget)

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, "default_error_messages", {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.validators = [*self.default_validators, *validators]

    def _setup_widget(self, widget):
        """Set up and configure the widget."""
        widget = widget or self.widget

        # If widget is a class, instantiate it
        if isinstance(widget, type):
            widget = widget(default_unit=self.default_unit, unit_choices=self.unit_choices)
        else:
            widget = copy.deepcopy(widget)

        # Trigger the localization machinery if needed.
        if self.localize:
            widget.is_localized = True

        # Let the widget know whether it should display as required.
        widget.is_required = self.required

        # Hook into self.widget_attrs() for any Field-specific HTML attributes.
        extra_attrs = self.widget_attrs(widget)
        if extra_attrs:
            widget.attrs.update(extra_attrs)

        if self.disabled:
            widget.attrs["disabled"] = True

        # If widget is not set, or is an admin widget, set it to use PintFieldWidget
        if widget is None or is_special_admin_widget(widget):
            widget = PintFieldWidget(default_unit=self.default_unit, unit_choices=self.unit_choices)
        else:
            if not hasattr(widget, "default_unit") or widget.default_unit is None:
                widget.default_unit = self.default_unit
            if not hasattr(widget, "unit_choices") or not widget.unit_choices:
                widget.unit_choices = self.unit_choices

        self.widget = widget
        return widget

    def prepare_value(self, value: Any) -> list:
        """Convert value to format expected by the widget."""
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return value

        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                comparator, magnitude, units = value  # pylint: disable=W0612
                return [magnitude, units]
            except ValueError:
                logger.warning("Invalid value %s for PintField", value)
                return [value, self.default_unit]

        if isinstance(value, Quantity):
            return [value.magnitude, value.units]

        if isinstance(value, str):
            try:
                comparator, magnitude, units = value.strip("()").split(",")
                return [Decimal(magnitude.strip()), str(units.strip())]
            except ValueError:
                return [value, self.default_unit]

        return [value, self.default_unit]

    def to_python(self, value) -> Optional[Quantity]:
        """Convert input value to a Quantity object."""
        if not value:
            return None

        if not isinstance(value, (list, tuple)):
            raise ValidationError(
                _("Value type %(value)s is invalid"),
                code="invalid_list",
                params={"value": type(value)},
            )

        if not self.required and value[0] == "":
            return None

        validate_required_value(value[0], required=True)
        validate_required_value(value[1], required=True)
        validate_value_range(value[0], self.min_value, self.max_value)

        try:
            converter = QuantityConverter(
                default_unit=self.default_unit,
                field_type="integer" if isinstance(self, IntegerPintFormField) else "decimal",
                unit_registry=self.ureg,
            )
            quantity = converter.convert(value)
            validate_dimensionality(quantity, self.default_unit)
            return quantity
        except (ValueError, TypeError) as e:
            raise ValidationError(str(e)) from e

    def clean(self, value: Any) -> Quantity:
        """Clean and validate the value."""
        if value in self.empty_values and self.required:
            raise ValidationError(self.error_messages["required"])

        value = self.to_python(value)

        # Convert min/max values to Quantities if they're not already
        min_value = self.min_value
        if min_value is not None and not isinstance(min_value, Quantity):
            min_value = self.ureg.Quantity(min_value, self.default_unit)

        max_value = self.max_value
        if max_value is not None and not isinstance(max_value, Quantity):
            max_value = self.ureg.Quantity(max_value, self.default_unit)

        # Validate the range using the potentially converted min/max values
        validate_value_range(value, min_value, max_value)

        self.validate(value)
        self.run_validators(value)
        return value


class IntegerPintFormField(BasePintFormField):
    """A form field to choose which unit to use to enter a value which is saved to the composite field.

    Used for Integer and BigInteger magnitudes.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the integer Pint form field."""
        super().__init__(*args, **kwargs)

        self.min_value = kwargs.pop("min_value", -9223372036854775808)
        self.max_value = kwargs.pop("max_value", 9223372036854775807)


class DecimalPintFormField(BasePintFormField):
    """A form field to choose which unit to use to enter a value, which is saved to the composite field."""

    def __init__(
        self,
        *,
        max_digits: Optional[int] = None,
        decimal_places: Optional[int] = None,
        display_decimal_places: Optional[int] = None,
        rounding_method: str = "ROUND_HALF_UP",
        **kwargs,
    ):
        """Initialize the decimal Pint form field."""

        # Deprecated options
        if decimal_places is not None or max_digits is not None:
            warnings.warn(
                "max_digits and decimal_places are deprecated and will be removed in a future version. "
                "Rely on Python's decimal precision instead.",
                DeprecationWarning,
            )

        if display_decimal_places and (not isinstance(display_decimal_places, int) or display_decimal_places < 0):
            raise ValidationError("If provided, display_decimal_places must be a positive integer or zero.")
        self.display_decimal_places = display_decimal_places
        self.rounding_method = rounding_method

        super().__init__(**kwargs)

        # Update widget attributes to control displayed precision if necessary
        if isinstance(self.widget, PintFieldWidget) and self.display_decimal_places is not None:
            self.widget.widgets[0].attrs["step"] = str(10**-self.display_decimal_places)

    def prepare_value(self, value):
        """Format the value for display using display_decimal_places."""
        value = super().prepare_value(value)

        if value and value[0] is not None and self.display_decimal_places is not None:
            try:
                decimal_value = Decimal(str(value[0]))  # Convert to Decimal for quantizing
                if self.display_decimal_places is not None:
                    # Quantize the value to the display_decimal_places
                    quantizing_string = get_quantizing_string(decimal_places=self.display_decimal_places)
                    formatted_value = decimal_value.quantize(Decimal(quantizing_string))
                else:
                    # Normalize the value to remove trailing zeros
                    formatted_value = decimal_value.normalize()
                    self.display_decimal_places = formatted_value.as_tuple().exponent
                return [formatted_value, value[1]]
            except (TypeError, ValueError, InvalidOperation):
                pass
        return value

    def to_python(self, value) -> Optional[Quantity]:
        """Convert input value to a Quantity with proper decimal handling."""
        quantity = super().to_python(value)

        if hasattr(quantity, "magnitude") and isinstance(quantity.magnitude, Decimal):
            validate_decimal_precision(quantity)
        else:
            try:
                quantity = self.ureg.Quantity(quantity)
            except Exception as e:
                raise ValidationError(
                    _("Unable to convert value to Quantity object."),
                    code="invalid_decimal",
                ) from e

        return quantity
