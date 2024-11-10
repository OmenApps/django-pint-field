"""Form fields for the Django Pint Field package."""

import copy
import logging
from decimal import Decimal
from decimal import InvalidOperation
from typing import Any
from typing import Optional
from typing import Union

from django import forms
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .helpers import check_matching_unit_dimension
from .helpers import get_quantizing_string
from .units import ureg
from .validation import QuantityConverter
from .validation import validate_decimal_places
from .validation import validate_dimensionality
from .validation import validate_required_value
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

    def __init__(  # pylint: disable=W0231
        self,
        *,
        default_unit: str,
        unit_choices: Optional[Union[list[str], tuple[str]]] = None,
        required=True,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        error_messages=None,
        show_hidden_initial=False,
        validators=(),
        localize=False,
        disabled=False,
        label_suffix=None,
    ):
        """Initialize the Pint form field."""
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

        if default_unit is None:
            raise ValidationError("PintFormField requires a default_unit kwarg of a single unit type (eg: 'grams')")
        self.default_unit = default_unit

        self.unit_choices = unit_choices or [self.default_unit]
        if self.default_unit not in self.unit_choices:
            self.unit_choices.append(self.default_unit)

        for choice in self.unit_choices:
            check_matching_unit_dimension(self.ureg, self.default_unit, [choice])

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

        self.min_value = kwargs.pop("min_value", -2147483648)
        self.max_value = kwargs.pop("max_value", 2147483647)


class DecimalPintFormField(BasePintFormField):
    """A form field to choose which unit to use to enter a value, which is saved to the composite field."""

    def __init__(self, *, max_digits: int, decimal_places: int, display_decimal_places: Optional[int] = None, **kwargs):
        """Initialize the decimal Pint form field."""
        if max_digits is None or not isinstance(max_digits, int):
            raise ValidationError("PintFormField requires a max_digits kwarg")
        self.max_digits = max_digits

        if decimal_places is None or not isinstance(decimal_places, int):
            raise ValidationError("PintFormField requires a decimal_places kwarg")
        self.decimal_places = decimal_places

        if self.decimal_places > self.max_digits:
            raise ValidationError("decimal_places cannot be greater than max_digits")

        if self.decimal_places < 0 or self.max_digits < 0:
            raise ValidationError("decimal_places and max_digits must be non-negative integers")

        if self.max_digits == 0:
            raise ValidationError("max_digits must be a positive integer")

        self.display_decimal_places = display_decimal_places if display_decimal_places is not None else decimal_places
        if not isinstance(self.display_decimal_places, int) or self.display_decimal_places < 0:
            raise ValidationError("display_decimal_places must be a non-negative integer")
        if self.display_decimal_places > self.decimal_places:
            raise ValidationError("display_decimal_places cannot be greater than decimal_places")

        super().__init__(**kwargs)

        # Update widget attributes to control displayed precision
        if isinstance(self.widget, PintFieldWidget):
            self.widget.widgets[0].attrs["step"] = str(10**-self.display_decimal_places)

    def prepare_value(self, value):
        """Format the value for display using display_decimal_places."""
        value = super().prepare_value(value)

        if value and value[0] is not None:
            try:
                decimal_value = Decimal(str(value[0]))
                formatted_value = decimal_value.quantize(Decimal(f"0.{'0' * self.display_decimal_places}"))
                return [formatted_value, value[1]]
            except (TypeError, ValueError, InvalidOperation):
                pass
        return value

    def to_python(self, value) -> Optional[Quantity]:
        """Convert input value to a Quantity with proper decimal handling."""
        quantity = super().to_python(value)

        if quantity is not None:
            validate_decimal_places(quantity, self.decimal_places, self.max_digits)

            # Quantize the decimal value
            magnitude = Decimal(str(quantity.magnitude))
            quantizing_string = get_quantizing_string(self.max_digits, self.decimal_places)
            try:
                new_magnitude = magnitude.quantize(Decimal(quantizing_string))
                return self.ureg.Quantity(new_magnitude * getattr(self.ureg, str(quantity.units)))
            except InvalidOperation as e:
                raise ValidationError(
                    _("Unable to quantize to specified precision"),
                    code="invalid_decimal",
                ) from e

        return quantity
