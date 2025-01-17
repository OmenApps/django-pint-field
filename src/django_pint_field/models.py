"""Django Pint Field models."""

from __future__ import annotations

import decimal
import logging
import warnings
from collections.abc import Iterable  # pylint: disable=E0611
from decimal import Decimal
from enum import Enum
from typing import Any
from typing import Optional

import psycopg
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import connection
from django.db import models
from django.db.backends.base.base import NO_DB_ALIAS
from django.db.models import Field
from django.utils.translation import gettext_lazy as _
from pint import Quantity as BaseQuantity
from pint.errors import UndefinedUnitError
from psycopg.types.composite import CompositeInfo
from psycopg.types.composite import register_composite

from django_pint_field.helpers import get_quantizing_string

from .adapters import PintDumper
from .forms import DecimalPintFormField
from .forms import IntegerPintFormField
from .helpers import PintFieldConverter
from .helpers import PintFieldProxy
from .helpers import check_matching_unit_dimension
from .helpers import get_pint_unit
from .units import ureg
from .validation import QuantityConverter
from .validation import validate_decimal_precision
from .validation import validate_dimensionality
from .validation import validate_required_value
from .validation import validate_unit_choices


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity


def create_quantity_from_composite(comparator, magnitude, units):  # pylint: disable=W0621 disable=W0613
    """Factory function to create a Quantity from composite data."""
    quantity_obj = Quantity(Decimal(magnitude), units)
    return quantity_obj


def register_pint_composite_types(sender, **kwargs):  # pylint: disable=W0621 disable=W0613
    """Register the composite types and adapters for the PintField."""
    if connection.vendor != "postgresql" or connection.alias == NO_DB_ALIAS:
        return

    conn = connection.connection  # This is the psycopg3 connection

    try:
        # Fetch and register the single composite type
        comp_info = CompositeInfo.fetch(conn, "pint_field")
        if comp_info is not None:
            register_composite(info=comp_info, context=None, factory=create_quantity_from_composite)
    except Exception as e:  # pylint: disable=W0718
        logger.error("Error registering composite type pint_field: %s", e)

    # Register the dumper for Quantity objects in the connection's context
    # conn.adapters.register_dumper(Quantity, PintDumper)


psycopg.adapters.register_dumper(Quantity, PintDumper)


class FieldType(Enum):
    """Enumeration of the field types for the PintField."""

    NONE_FIELD = 0
    INTEGER_FIELD = 1
    BIG_INTEGER_FIELD = 2
    DECIMAL_FIELD = 3


class PintFieldDescriptor:
    """Descriptor for handling PintField attribute access and unit conversions."""

    def __init__(self, field: Field):
        """Initialize the descriptor with the field instance."""
        self.field = field
        self.converter = PintFieldConverter(field)

    def __get__(self, instance, owner=None):
        """Return the descriptor or a proxy object for the field value."""
        if instance is None:
            return self

        value = instance.__dict__.get(self.field.name)
        if value is None:
            return None

        # Return a proxy object that handles unit conversions
        return PintFieldProxy(value, self.converter)


class PintFieldMixin:
    """Mixin that adds unit conversion capabilities to PintFields."""

    @staticmethod
    def create_unit_property(unit_name: str, name: str):
        """Create a property that handles the unit conversion."""

        def getter(instance):
            field = instance._meta.get_field(name)  # pylint: disable=W0212
            value = getattr(instance, name)
            if value is None:
                return None

            try:
                if isinstance(value, PintFieldProxy):
                    value = value.quantity
                converted = value.to(unit_name)

                # Format according to display_decimal_places if set
                display_decimal_places = getattr(field, "display_decimal_places", None)
                if display_decimal_places is not None:
                    magnitude = float(converted.magnitude)
                    formatted_magnitude = f"{magnitude:.{display_decimal_places}f}"
                    # Remove trailing zeros after decimal point, but keep the decimal point if places > 0
                    if "." in formatted_magnitude:
                        formatted_magnitude = formatted_magnitude.rstrip("0").rstrip(".")
                    return f"{formatted_magnitude} {converted.units}"

                return converted

            except (AttributeError, UndefinedUnitError) as e:
                logger.error("Error converting value to %s: %s", unit_name, e)
                return None

        return property(getter)

    def add_properties(self, cls, name):
        """Add properties for all common units that match the dimensionality."""
        base_unit = get_pint_unit(self.ureg, self.default_unit)
        for unit_name in dir(self.ureg):
            if unit_name.startswith("_"):
                continue

            try:
                unit = get_pint_unit(self.ureg, unit_name)
                if not hasattr(unit, "dimensionality"):
                    continue

                if unit.dimensionality == base_unit.dimensionality:
                    property_name = f"{name}__{unit_name}"
                    setattr(cls, property_name, self.create_unit_property(unit_name, name))
            except (KeyError, AttributeError, UndefinedUnitError):
                continue

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        """Extend the model class with unit conversion methods."""
        super().contribute_to_class(cls, name, private_only, **kwargs)

        # Set the descriptor
        setattr(cls, name, PintFieldDescriptor(self))

        # Add properties for all common units that match the dimensionality
        self.add_properties(cls, name)

        # Don't override a get_FOO_display() method defined explicitly on the class
        if f"get_{self.name}_display" not in cls.__dict__:

            def get_display(obj, digits=None, format_string=None):
                return self._get_FIELD_display(obj, digits, format_string)

            setattr(cls, f"get_{self.name}_display", get_display)


class BasePintField(PintFieldMixin, models.Field):
    """A Django Model Field that resolves to a pint object."""

    field_type = FieldType.NONE_FIELD
    form_field_class = IntegerPintFormField
    FIELD_NAME = ""  # Set by child classes
    empty_values = list(validators.EMPTY_VALUES)

    def __init__(
        self,
        *args,
        default_unit: str | tuple[str, str] | list[str, str],
        unit_choices: Optional[Iterable[str] | Iterable[Iterable[str]]] = None,
        verbose_name: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Pint field."""
        if not isinstance(default_unit, (str, list, tuple)):
            raise ValidationError(
                "Django Pint Fields must be defined with a default_unit of type str or "
                f"2-tuple/2-list, but got type: {type(default_unit)}"
            )

        # Normalize default_unit to a 2-tuple format
        if isinstance(default_unit, str):
            self._default_unit_display = default_unit
            self._default_unit_value = default_unit
        elif len(default_unit) == 2:
            self._default_unit_display, self._default_unit_value = default_unit
        else:
            raise ValidationError(
                "When providing default_unit as a tuple/list, it must contain exactly 2 elements: "
                "(display_name, unit_value)"
            )

        try:
            self.ureg = ureg
            get_pint_unit(self.ureg, self._default_unit_value)
        except AttributeError as e:
            raise ValidationError(f"Invalid unit: {self._default_unit_value}") from e

        self.verbose_name = verbose_name
        self.name = name
        self.default_unit = self._default_unit_value  # For backwards compatibility

        # Validate and normalize unit choices
        normalized_choices = validate_unit_choices(unit_choices, self.default_unit)
        # Extract just the unit values for dimensionality checking
        unit_values = [choice[1] for choice in normalized_choices]

        self.unit_choices = self.setup_unit_choices(normalized_choices)

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, unit_values)

        super().__init__(*args, **kwargs)

    def setup_unit_choices(self, unit_choices: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """Set up unit choices ensuring default unit is the first option."""
        if not unit_choices:
            return [(self.default_unit, self.default_unit)]

        # Remove any choice that has default_unit as the value
        unit_choices = [choice for choice in unit_choices if choice[1] != self.default_unit]
        # Add default unit as first choice
        return [(self.default_unit, self.default_unit), *unit_choices]

    def db_type(self, connection) -> str:  # pylint: disable=W0621 disable=W0613
        """Returns the database column data type for this field."""
        return "pint_field"

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        """Add the field to the model class."""
        super().contribute_to_class(cls, name, private_only=private_only, **kwargs)
        setattr(cls, self.name, self)

    def _get_FIELD_display(self, obj: Quantity, digits=None, format_string=None):  # pylint: disable=C0103
        """Return the display value for a PintField."""
        value = getattr(obj, self.attname)
        if value is None:
            return ""

        if isinstance(value, PintFieldProxy):
            value = value.quantity

        if self.field_type == FieldType.INTEGER_FIELD:
            return f"{value:.0f}"

        if isinstance(value, BaseQuantity):
            # Convert to Quantity
            value = self.fix_unit_registry(value)

        if digits is not None:
            quantizing_string = get_quantizing_string(decimal_places=digits)
            quantized_magnitude = Decimal(value.magnitude).quantize(Decimal(quantizing_string))
        elif hasattr(self, "display_decimal_places") and self.display_decimal_places:
            quantizing_string = get_quantizing_string(decimal_places=self.display_decimal_places)
            quantized_magnitude = Decimal(value.magnitude).quantize(Decimal(quantizing_string))
        else:
            quantized_magnitude = value.magnitude


        if format_string is not None:
            return f"{Quantity(quantized_magnitude, value.units):{format_string}}"

        return f"{Quantity(quantized_magnitude, value.units)}"

    def deconstruct(self):
        """Return enough information to recreate the field as a 4-tuple.

        * The name of the field on the model, if contribute_to_class() has been run.
        * The import path of the field, including the class: e.g. django.db.models.IntegerField
          This should be the most portable version, so less specific may be better.
        * A list of positional arguments.
        * A dict of keyword arguments.
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs["default_unit"] = self.default_unit
        kwargs["unit_choices"] = self.unit_choices

        if self.field_type == FieldType.DECIMAL_FIELD:
            kwargs["rounding_method"] = getattr(self, "rounding_method", None)
            kwargs["display_decimal_places"] = getattr(self, "display_decimal_places", None)

        return name, path, args, kwargs

    def fix_unit_registry(self, value: BaseQuantity | Quantity) -> Quantity:
        """Check if the UnitRegistry from settings is used. If not try to fix it but give a warning."""
        if value is None:
            return value

        if not isinstance(value, (BaseQuantity, self.ureg.Quantity)):
            raise ValidationError("If provided, value must be a Quantity")

        if not isinstance(value, self.ureg.Quantity):
            warnings.warn(
                "Unit registry mismatch detected. Converting to use the same unit registry.",
                RuntimeWarning,
            )
            converter = QuantityConverter(
                default_unit=self.default_unit,
                field_type="decimal" if self.field_type == FieldType.DECIMAL_FIELD else "integer",
                unit_registry=self.ureg,
            )
            return converter.convert(value)
        return value

    def get_prep_value(self, value):
        """Converts Python objects to query values."""
        if value in self.empty_values:
            return value

        if isinstance(value, PintFieldProxy):
            value = value.quantity  # Unwrap proxy before preparing value

        # If we're doing a range query, handle each value individually
        if (
            isinstance(value, (tuple, list))
            and len(value) == 2
            and isinstance(value[0], Quantity)
            and isinstance(value[1], Quantity)
        ):
            return [self.get_prep_value(v) for v in value]

        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal" if self.field_type == FieldType.DECIMAL_FIELD else "integer",
            unit_registry=self.ureg,
        )
        value = converter.convert(value)

        if isinstance(value, BaseQuantity):
            value = self.fix_unit_registry(value)

        validate_dimensionality(value, self.default_unit)

        # Note: We intentionally don't validate decimal places here
        # to allow database operations to work with full precision
        return value

    def from_db_value(self, value, expression, connection):  # pylint: disable=W0613
        """Convert database value to Python object."""
        if value is None:
            return None

        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal",
            unit_registry=self.ureg,
        )
        converted = converter.convert(value)
        if converted is None:
            return None

        # Always wrap in our new, pickle-friendly PintFieldProxy
        converter = PintFieldConverter(self)
        return PintFieldProxy(converted, converter)

    def to_python(self, value):
        """Converts the value into the correct Python object."""
        if isinstance(value, PintFieldProxy):
            return value.quantity  # Unwrap proxy when converting to Python

        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal" if self.field_type == FieldType.DECIMAL_FIELD else "integer",
            unit_registry=self.ureg,
        )
        return converter.convert(value)

    def value_from_object(self, obj):
        """Get the value from the object."""
        value = super().value_from_object(obj)
        if isinstance(value, PintFieldProxy):
            return value.quantity  # Return unwrapped value for form fields
        return value

    def value_to_string(self, obj):
        """Convert the value to a string, respecting display_decimal_places, if applicable."""
        value = self.value_from_object(obj)
        if isinstance(value, PintFieldProxy):
            return str(value)
        return str(value) if value is not None else ""

    def validate(self, value, model_instance):
        """Validate value and raise ValidationError if necessary."""
        if not self.editable:
            return

        validate_required_value(value, required=not self.null, blank=self.blank)
        validate_dimensionality(value, self.default_unit)

        if self.choices is not None and value not in self.empty_values:
            for option_key, option_value in self.choices:
                if isinstance(option_value, (list, tuple)):
                    # This is an optgroup, so look inside the group for options.
                    for optgroup_key, _optgroup_value in option_value:
                        if value == optgroup_key:
                            return
                elif value == option_key:
                    return
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

    def clean(self, value, model_instance) -> BaseQuantity:
        """Convert the value's type and run validation."""
        value = self.to_python(value)
        self.validate(value, model_instance)
        self.run_validators(value)
        return value

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        """Return a form field for this model field."""
        defaults = {
            "form_class": self.form_field_class,
            "default_unit": self.default_unit,
            "unit_choices": self.unit_choices,
            "label": self.name.capitalize() if self.name is not None else "Pint Field",
        }
        if self.field_type == FieldType.DECIMAL_FIELD:
            defaults["rounding_method"] = getattr(self, "rounding_method", None)
            defaults["display_decimal_places"] = getattr(self, "display_decimal_places", None)
        defaults.update(kwargs)
        return super().formfield(**defaults)


class IntegerPintField(BasePintField):
    """A Django Model Field that resolves to a pint object with integer values."""

    description = _("A Django Model Field that resolves to an Integer-based pint object.")
    field_type = FieldType.INTEGER_FIELD
    FIELD_NAME = "IntegerField"


class BigIntegerPintField(IntegerPintField):
    """A Django Model Field that resolves to a pint object with integer values.

    This field is deprecated and will be removed in a future release. Instead, use IntegerPintField, which now
    provides the same functionality.
    """

    description = _("This field is deprecated and will be removed in a future release. Instead, use IntegerPintField.")
    field_type = FieldType.BIG_INTEGER_FIELD
    FIELD_NAME = "BigIntegerField"


class DecimalPintField(BasePintField):
    """A Django Model Field that resolves to a pint object with decimal values."""

    description = _("A Django Model Field that resolves to a Decimal-based pint object.")
    field_type = FieldType.DECIMAL_FIELD
    form_field_class = DecimalPintFormField

    def __init__(
        self,
        *args,
        max_digits: Optional[int] = None,
        decimal_places: Optional[int] = None,
        display_decimal_places: Optional[int] = None,
        rounding_method: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Decimal Pint field."""

        # Deprecated options
        if decimal_places is not None or max_digits is not None:
            warnings.warn(
                "max_digits and decimal_places are deprecated and will be removed in a future version. "
                "Rely on Python's decimal precision instead.",
                DeprecationWarning,
            )

        self.display_decimal_places = display_decimal_places
        self.rounding_method = rounding_method

        self._check_arguments()

        super().__init__(*args, **kwargs)

    def _check_arguments(self):
        """Check if the arguments are valid."""

        # Check if display_decimal_places is greater than the current decimal precision
        if self.display_decimal_places is not None and self.display_decimal_places > decimal.getcontext().prec:
            raise ValidationError(
                "display_decimal_places must be less than or equal to the current decimal precision: "
                f"{decimal.getcontext().prec}"
            )

        if self.rounding_method is not None:
            valid_rounding_methods = [v for k, v in vars(decimal).items() if k.startswith("ROUND_")]
            if self.rounding_method not in valid_rounding_methods:
                raise ValidationError(
                    f"Invalid rounding_method option {self.rounding_method}. "
                    f"If provided, rounding_method must be one of: {valid_rounding_methods}"
                )

    def _should_skip_validation(self, value, model_instance) -> bool:
        """Determine if we should skip decimal place validation for this value.

        We skip validation in these cases:
        1. Value is None or empty
        2. Value comes from a database aggregation/computation
        3. Value is being loaded from the database (not a form or direct assignment)
        """
        if value is None or value in self.empty_values:
            return True

        # Check if this is part of a database operation by looking at the model instance
        if model_instance is not None and model_instance._state.adding is False:
            # If this is an existing model instance and we're loading data,
            # skip validation as it's coming from the database
            return True

        # Get the current frame's locals to check context
        import inspect  # pylint: disable=C0415

        frame = inspect.currentframe()
        try:
            while frame is not None:
                # Check if we're in an aggregation operation
                if "self" in frame.f_locals:
                    f_self = frame.f_locals["self"]
                    if any(
                        aggregation_class in f_self.__class__.__name__
                        for aggregation_class in ["Aggregate", "PintSum", "PintAvg"]
                    ):
                        return True
                frame = frame.f_back
        finally:
            del frame  # Clean up circular reference

        return False

    def validate(self, value, model_instance):
        """Validate the value and raise ValidationError if necessary.

        Only validates decimal precision when the value is being set directly
        or through a form. Skips these validations during database operations.
        """
        super().validate(value, model_instance)

        if not self._should_skip_validation(value, model_instance):
            validate_decimal_precision(value, allow_rounding=self.rounding_method is not None)

    def clean(self, value: Any, model_instance: Optional[models.Model]) -> BaseQuantity:
        """Convert the value's type and run validation."""
        if value is None:
            if self.null:
                return None
            raise ValidationError(self.error_messages["null"])

        if hasattr(value, "magnitude") and self.rounding_method:
            try:
                _ = value.magnitude
            except (TypeError, ValueError) as e:
                raise ValidationError(str(e)) from e

        return super().clean(value, model_instance)

    def format_value(self, value):
        """Format a value with the proper decimal places."""
        if value is None:
            return ""

        if hasattr(value, "magnitude") and self.display_decimal_places is not None:
            # Format the magnitude to the specified decimal places
            magnitude = float(value.magnitude)
            formatted_magnitude = f"{magnitude:.{self.display_decimal_places}f}"
            # Remove trailing zeros after decimal point, but keep the decimal point if places > 0
            if "." in formatted_magnitude:
                formatted_magnitude = formatted_magnitude.rstrip("0").rstrip(".")
            return f"{formatted_magnitude} {value.units}"

        return str(value)

    def get_db_prep_save(self, value, connection) -> Decimal:  # pylint: disable=W0621
        """Get value that shall be saved to database."""
        if value is None:
            return value

        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal",
            unit_registry=self.ureg,
        )
        value = converter.convert(value)

        if self.rounding_method and value is not None:
            magnitude = value.magnitude
            if not isinstance(magnitude, Decimal):
                try:
                    magnitude = Decimal(str(magnitude))
                except (TypeError, ValueError) as e:
                    raise ValidationError(str(e)) from e
        else:
            self.validate(value, None)

        return self.get_prep_value(value)
