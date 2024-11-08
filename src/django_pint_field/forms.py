"""Form fields for the Django Pint Field package."""

import copy
import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from django import forms
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from pint import DimensionalityError, Quantity

from .helper import (
    check_matching_unit_dimension,
    get_quantizing_string,
    is_decimal_or_int,
)
from .units import ureg
from .widgets import PintFieldWidget

DJANGO_JSON_SERIALIZABLE_BASE = Union[None, bool, str, int, float, complex, datetime.datetime]
DJANGO_JSON_SERIALIZABLE = Union[Sequence[DJANGO_JSON_SERIALIZABLE_BASE], Dict[str, DJANGO_JSON_SERIALIZABLE_BASE]]
NUMBER_TYPE = Union[int, float, Decimal]


def is_special_admin_widget(widget) -> bool:
    """
    There are some special django admin widgets, defined
    in django/contrib/admin/options.py in the variable
    FORMFIELD_FOR_DBFIELD_DEFAULTS
    The intention for Integer and BigIntegerField is only to
    define the width.

    They are set through a complicated process of the
    modelform_factory setting formfield_callback to
    ModelForm.formfield_to_dbfield

    As they will overwrite our Widget we check for them and
    will ignore them, if they are set as attribute.

    We still will allow subclasses, so the end user has still
    the possibility to use this widget.
    """
    WIDGETS_TO_IGNORE = [
        FORMFIELD_FOR_DBFIELD_DEFAULTS[models.IntegerField],
        FORMFIELD_FOR_DBFIELD_DEFAULTS[models.BigIntegerField],
    ]
    classes_to_ignore = [ignored_widget["widget"].__name__ for ignored_widget in WIDGETS_TO_IGNORE]

    widget_class_name = getattr(widget, "__name__", None) or getattr(widget, "__class__").__name__
    return widget_class_name in classes_to_ignore


class BasePintFormField(forms.Field):
    """Base form field to choose which unit to use to enter a value which is saved to the composite field.

    Some of the __init__() logic is copied from the django.forms.fields.Field class, because simply calling
    `super().__init__(*args, **kwargs)` would overwrite the widget attribute.
    """

    widget = PintFieldWidget

    validate: Callable
    run_validators: Callable
    error_messages: Dict[str, str]
    empty_values: Sequence[Any]
    localize: bool

    # def __init__(self, *args, **kwargs):  # pylint: disable=W0231
    def __init__(
        self,
        *,
        default_unit: str,
        unit_choices: Optional[Union[List[str], Tuple[str]]] = None,
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
        self.ureg = ureg

        self.required = required
        self.label = label
        self.initial = initial
        self.show_hidden_initial = show_hidden_initial
        self.help_text = help_text
        self.disabled = disabled
        self.label_suffix = label_suffix
        self.localize = localize

        if default_unit is None:
            raise ValueError("PintFormField requires a default_unit kwarg of a single unit type (eg: 'grams')")
        self.default_unit = default_unit

        self.unit_choices = unit_choices or [self.default_unit]
        if self.default_unit not in self.unit_choices:
            self.unit_choices.append(self.default_unit)

        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

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

        # If widget is not set, or is an admin widget, set it to use PintFieldWidget
        if widget is None or is_special_admin_widget(widget):
            widget = PintFieldWidget(default_unit=self.default_unit, unit_choices=self.unit_choices)
        else:
            if not hasattr(widget, "default_unit") or widget.default_unit is None:
                widget.default_unit = self.default_unit
            if not hasattr(widget, "unit_choices") or not widget.unit_choices:
                widget.unit_choices = self.unit_choices

        self.widget = widget

        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, "default_error_messages", {}))
        messages.update(error_messages or {})
        self.error_messages = messages

        self.validators = [*self.default_validators, *validators]

    def prepare_value(self, value):
        """Prepare the value for the widget."""

        return value

    def to_python(self, value) -> ureg.Quantity:
        """Return an ureg.Quantity python object from the input value."""
        if not value:
            raise ValidationError(
                _("Value not provided"),
                code="no_value",
            )

        if not isinstance(value, (list, tuple)):
            raise ValidationError(
                _("Value type %(value)s is invalid"),
                code="invalid_list",
                params={"value": type(value)},
            )

        if not self.required and value[0] == "":
            return value

        if not value[0] or not value[1]:
            raise ValidationError(
                _("Value (%(value)s) cannot be NoneType"),
                code="value_is_nonetype",
                params={"value": type(value)},
            )

        if value[0] == "" or value[1] == "":
            raise ValidationError(
                _("Value (%(value)s) cannot be blank"),
                code="value_is_blank",
                params={"value": type(value)},
            )

        if not is_decimal_or_int(value[0]):
            raise ValidationError(
                _("%(value)s is invalid"),
                code="invalid_number",
                params={"value": value[0]},
            )

        try:
            check_matching_unit_dimension(
                self.ureg,
                self.default_unit,
                [
                    value[1],
                ],
            )
        except DimensionalityError as e:
            raise ValidationError(
                _("%(value)s is has invalid dimensionality"),
                code="invalid_dimensionality",
                params={"value": value},
            ) from e

        return value

    def clean(self, value):
        """Validate the given value and return its "cleaned" value as an appropriate Python object.

        Raise ValidationError for any errors.
        """
        value = self.to_python(value)
        # value here is a Quantity object. e.g.: <Quantity(3, 'pound')>
        self.validate(value)
        self.run_validators(value)
        return value


class IntegerPintFormField(BasePintFormField):
    """A form field to choose which unit to use to enter a value which is saved to the composite field.

    Used for Integer and BigInteger magnitudes.
    """

    def __init__(self, *args, **kwargs):
        self.min_value = kwargs.pop("min_value", -2147483648)
        self.max_value = kwargs.pop("max_value", 2147483647)

        super().__init__(*args, **kwargs)

    def to_python(self, value) -> ureg.Quantity:
        """Return an ureg.Quantity python object from the input value."""
        value = super().to_python(value)

        if is_decimal_or_int(value[0]) > self.max_value:
            raise ValidationError(
                _("%(value)s is too large"),
                code="number_too_large",
                params={"value": value[0]},
            )

        if is_decimal_or_int(value[0]) < self.min_value:
            raise ValidationError(
                _("%(value)s is too small"),
                code="number_too_small",
                params={"value": value[0]},
            )

        return self.ureg.Quantity(int(float(value[0])) * getattr(self.ureg, value[1]))


class DecimalPintFormField(BasePintFormField):
    """A form field to choose which unit to use to enter a value, which is saved to the composite field."""

    def __init__(self, *, max_digits: int, decimal_places: int, **kwargs):
        self.min_value = kwargs.pop("min_value", None)  # Not used, but gets passed in via BasePintField
        self.max_value = kwargs.pop("max_value", None)  # Not used, but gets passed in via BasePintField

        if max_digits is None or not isinstance(max_digits, int):
            raise ValueError("PintFormField requires a max_digits kwarg")
        self.max_digits = max_digits

        if decimal_places is None or not isinstance(decimal_places, int):
            raise ValueError("PintFormField requires a decimal_places kwarg")
        self.decimal_places = decimal_places

        super().__init__(**kwargs)

    def prepare_value(self, value):
        """Prepare the value for the widget."""
        super().prepare_value(value)

        if isinstance(value, Quantity):
            # quantize the decimal value so we can validate is is no longer than max_digits after quantization
            quantizing_string = get_quantizing_string(max_digits=self.max_digits, decimal_places=self.decimal_places)
            new_magnitude = Decimal(str(value.magnitude)).quantize(Decimal(quantizing_string))

            value = self.ureg.Quantity(new_magnitude * getattr(self.ureg, str(value.units)))

        return value

    def to_python(self, value) -> ureg.Quantity:
        """Return an ureg.Quantity python object from the input value."""
        value = super().to_python(value)

        # quantize the decimal value so we can validate is is no longer than max_digits after quantization
        quantizing_string = get_quantizing_string(max_digits=self.max_digits, decimal_places=self.decimal_places)
        new_magnitude = Decimal(str(value[0])).quantize(Decimal(quantizing_string))

        if len(str(new_magnitude)) - 1 > self.max_digits:
            raise ValidationError(
                _(
                    "Unable to quantize %(value)s to max_digits of %(max_digits)s, "
                    "likely due to too many leading digits."
                ),
                code="exceeded_max_digits",
                params={"value": value[0], "max_digits": self.max_digits},
            )

        return self.ureg.Quantity(new_magnitude * getattr(self.ureg, value[1]))
