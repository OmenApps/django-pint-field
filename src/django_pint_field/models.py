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
from typing import Union

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

from .adapters import PintDumper
from .forms import DecimalPintFormField
from .forms import IntegerPintFormField
from .helpers import check_matching_unit_dimension
from .units import ureg
from .validation import QuantityConverter
from .validation import validate_decimal_places
from .validation import validate_dimensionality
from .validation import validate_required_value


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


class PintFieldConverter:
    """Handles unit conversions for PintField values in admin displays."""

    def __init__(self, field_instance: Field):
        """Initialize the converter with the field instance."""
        self.field = field_instance
        self.ureg = field_instance.ureg

    def convert_to_unit(self, value: Quantity, target_unit: str) -> Optional[Quantity]:
        """Convert a quantity to the target unit."""
        if value is None:
            return None

        try:
            target_unit_obj = getattr(self.ureg, target_unit)
            return value.to(target_unit_obj)
        except (AttributeError, UndefinedUnitError):
            return None


class PintFieldProxy:
    """Proxy for PintField values that enables unit conversion via attribute access."""

    def __init__(self, value: Quantity, converter: PintFieldConverter):
        """Initialize the proxy with the value and converter."""
        self.value = value
        self.converter = converter

    def __str__(self):
        """Return the string representation of the value."""
        return str(self.value)

    def __getattr__(self, name: str) -> Union[Quantity, str]:
        """Handle attribute access for unit conversions."""
        if name.startswith("__"):
            raise AttributeError(name)

        # If the attribute starts with get_, remove it
        if name.startswith("get_"):
            name = name[4:]

        # Convert the value to the requested unit
        converted = self.converter.convert_to_unit(self.value, name)
        if converted is not None:
            return converted

        raise AttributeError(f"Invalid unit conversion: {name}")


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
            value = getattr(instance, name)
            if value is None:
                return None
            try:
                return value.to(unit_name)
            except (AttributeError, UndefinedUnitError):
                return None

        return property(getter)

    def add_properties(self, cls, name):
        """Add properties for all common units that match the dimensionality."""
        base_unit = getattr(self.ureg, self.default_unit)
        for unit_name in dir(self.ureg):
            if unit_name.startswith("_"):
                continue

            try:
                unit = getattr(self.ureg, unit_name)
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


class BasePintField(PintFieldMixin, models.Field):
    """A Django Model Field that resolves to a pint object."""

    field_type = FieldType.NONE_FIELD
    form_field_class = IntegerPintFormField
    FIELD_NAME = ""  # Set by child classes
    empty_values = list(validators.EMPTY_VALUES)

    def __init__(
        self,
        *args,
        default_unit: str,
        unit_choices: Optional[Iterable[str]] = None,
        verbose_name: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Pint field."""
        if not default_unit or not isinstance(default_unit, str):
            raise ValidationError(
                "Django Pint Fields must be defined with a default_unit, eg: 'gram', "
                f"but default_value of type: {type(default_unit)} was provided"
            )

        try:
            self.ureg = ureg
            getattr(self.ureg, default_unit)
        except AttributeError as e:
            raise ValidationError(f"Invalid unit: {default_unit}") from e

        self.verbose_name = verbose_name
        self.name = name
        self.default_unit = default_unit
        self.unit_choices = self.setup_unit_choices(unit_choices)

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

        super().__init__(*args, **kwargs)

    def setup_unit_choices(self, unit_choices: Optional[Iterable[str]]) -> list[str]:
        """Set up unit choices ensuring default unit is the first option."""
        if unit_choices is None:
            return [self.default_unit]

        unit_choices = list(unit_choices)
        if self.default_unit in unit_choices:
            unit_choices.remove(self.default_unit)
        return [self.default_unit, *unit_choices]

    def db_type(self, connection) -> str:  # pylint: disable=W0621 disable=W0613
        """Returns the database column data type for this field."""
        return "pint_field"

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        """Add the field to the model class."""
        super().contribute_to_class(cls, name, private_only=private_only, **kwargs)
        setattr(cls, self.name, self)

    def deconstruct(self):
        """Return enough information to recreate the field as a 4-tuple.

        * The name of the field on the model, if contribute_to_class() has
          been run.
        * The import path of the field, including the class:e.g.
          django.db.models.IntegerField This should be the most portable
          version, so less specific may be better.
        * A list of positional arguments.
        * A dict of keyword arguments.
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs["default_unit"] = self.default_unit
        kwargs["unit_choices"] = self.unit_choices

        if self.field_type == FieldType.DECIMAL_FIELD:
            kwargs["max_digits"] = getattr(self, "max_digits", None)
            kwargs["decimal_places"] = getattr(self, "decimal_places", None)

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
        print(f"get_prep_value: {value=}")
        if value in self.empty_values:
            return value

        # If we're doing a range query, we need to check each quantity individually, so we recursively call this method
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

        return value

    def from_db_value(
        self, value, expression, connection  # pylint: disable=W0621 disable=W0613
    ) -> Optional[BaseQuantity]:
        """Converts a value as returned by the database to a Python object."""
        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal" if self.field_type == FieldType.DECIMAL_FIELD else "integer",
            unit_registry=self.ureg,
        )
        return converter.convert(value)

    def to_python(self, value):
        """Converts the value into the correct Python object."""
        converter = QuantityConverter(
            default_unit=self.default_unit,
            field_type="decimal" if self.field_type == FieldType.DECIMAL_FIELD else "integer",
            unit_registry=self.ureg,
        )
        return converter.convert(value)

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
            defaults["max_digits"] = getattr(self, "max_digits", None)
            defaults["decimal_places"] = getattr(self, "decimal_places", None)
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
        decimal_places: int,
        max_digits: int,
        rounding_method: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Decimal Pint field."""
        self.decimal_places = decimal_places
        self.max_digits = max_digits
        self.rounding_method = rounding_method

        if not isinstance(self.max_digits, int) or not isinstance(self.decimal_places, int):
            raise ValidationError(
                "Invalid initialization for DecimalPintField. "
                "max_digits and decimal_places must be provided as integers. "
                f"{self.max_digits=}, {self.decimal_places=}."
            )

        if self.decimal_places < 0 or self.max_digits < 1 or self.decimal_places > self.max_digits:
            raise ValidationError(
                "Invalid initialization for DecimalPintField. "
                "max_digits and decimal_places need to positive, and max_digits "
                "needs to be larger than decimal_places and at least 1. "
                f"{self.max_digits=} and {self.decimal_places=} "
                "are not valid parameters."
            )

        if self.rounding_method is not None:
            valid_rounding_methods = [v for k, v in vars(decimal).items() if k.startswith("ROUND_")]
            if self.rounding_method not in valid_rounding_methods:
                raise ValidationError(
                    f"Invalid rounding_method option {self.rounding_method}. "
                    f"If provided, rounding_method must be one of: {valid_rounding_methods}"
                )

        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        """Validate the value and raise ValidationError if necessary."""
        super().validate(value, model_instance)

        if value is not None and value not in self.empty_values:
            validate_decimal_places(
                value, self.decimal_places, self.max_digits, allow_rounding=self.rounding_method is not None
            )

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
                magnitude = Decimal(str(magnitude))
            value = self.ureg.Quantity(
                magnitude.quantize(Decimal(10) ** -self.decimal_places, rounding=self.rounding_method), value.units
            )
        else:
            self.validate(value, None)

        return self.get_prep_value(value)

    def clean(self, value: Any, model_instance: Optional[models.Model]) -> BaseQuantity:
        """Convert the value's type and run validation."""
        if value is None:
            if self.null:
                return None
            raise ValidationError(self.error_messages["null"])

        if hasattr(value, "magnitude") and self.rounding_method:
            try:
                magnitude = value.magnitude
                if not isinstance(magnitude, Decimal):
                    magnitude = Decimal(str(magnitude))
                return self.ureg.Quantity(
                    magnitude.quantize(Decimal(10) ** -self.decimal_places, rounding=self.rounding_method), value.units
                )
            except (TypeError, ValueError) as e:
                raise ValidationError(str(e)) from e

        return super().clean(value, model_instance)
