"""Django Pint Field models."""

import decimal
import warnings
from decimal import Decimal
from typing import Callable, Iterable, List, Optional, Union

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from pint import Quantity as BaseQuantity
from psycopg2.extensions import AsIs
from psycopg.types.composite import CompositeInfo, register_composite

from .forms import DecimalPintFormField, IntegerPintFormField
from .helper import (
    check_matching_unit_dimension,
    get_base_unit_magnitude,
    get_base_units,
    get_quantizing_string,
    is_decimal_or_int,
)
from .units import ureg

NONE_FIELD = {"to_number_type": int}
INTEGER_FIELD = {"to_number_type": int}
BIG_INTEGER_FIELD = {"to_number_type": int}
DECIMAL_FIELD = {"to_number_type": Decimal}


class BasePintField(models.Field):
    """A Django Model Field that resolves to a pint Pint object"""

    field_type = NONE_FIELD
    to_number_type: field_type.get("to_number_type")
    name: str
    validate: Callable
    run_validators: Callable
    form_field_class = IntegerPintFormField
    MAX_VAL = None  # Set by child classes
    FIELD_NAME = ""  # Set by child classes

    def __init__(
        self,
        *args,
        default_unit: str,
        unit_choices: Optional[Iterable[str]] = None,
        verbose_name: Optional[str] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Pint field.

        :param default_unit: Unit description of default unit
        :param unit_choices: If given the possible unit choices with the same dimension like the default_unit
        """
        if not isinstance(default_unit, str):
            raise ValueError(
                "Django Pint Fields must be defined with a default_unit, eg: 'gram', "
                f"but default_value of type: {type(default_unit)} was provided"
            )

        self.ureg = ureg

        # We do the folowing in order to raise an exception if an invalid unit was supplied.
        unit = getattr(self.ureg, default_unit)  # pylint: disable=unused-variable  # noqa: F841
        self.default_unit = default_unit

        # Set unit choices
        self.unit_choices = self.setup_unit_choices(unit_choices)

        # if unit_choices is None:
        #     self.unit_choices = [self.default_unit]
        # else:
        #     self.unit_choices = list(unit_choices)
        #     # Remove the default unit if present, since we will adjust its position later.
        #     if self.default_unit in self.unit_choices:
        #         self.unit_choices.remove(self.default_unit)

        #     # ToDo: Remove the selected unit if present, since we will adjust its position later.
        #     # if self.value.units in self.unit_choices:
        #     #    self.unit_choices.remove(self.value.units)

        #     # ToDo: If the model has been saved, the first unit in the select should be the saved unit
        #     # Default unit should be the first choice, always as all values are saved as
        #     # default unit within the database and this would be the first unit shown
        #     # in the widget
        #     self.unit_choices = [self.default_unit, *self.unit_choices]
        #     # ToDo: self.unit_choices = [self.value.units, self.default_unit, *self.unit_choices]

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

        super().__init__(*args, **kwargs)

    def setup_unit_choices(self, unit_choices: Optional[Iterable[str]]) -> List[str]:
        """Set up unit choices ensuring default unit is the first option."""
        if unit_choices is None:
            return [self.default_unit]
        unit_choices = list(unit_choices)
        if self.default_unit in unit_choices:
            unit_choices.remove(self.default_unit)
        return [self.default_unit, *unit_choices]

    def db_type(self, connection) -> str:  # pylint: disable=unused-argument
        """Returns the database column data type for this field."""
        if self.field_type == INTEGER_FIELD:
            return "integer_pint_field"
        if self.field_type == BIG_INTEGER_FIELD:
            return "big_integer_pint_field"
        return "decimal_pint_field"

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

        if self.field_type == DECIMAL_FIELD:
            kwargs["max_digits"] = getattr(self, "max_digits", None)
            kwargs["decimal_places"] = getattr(self, "decimal_places", None)

        return name, path, args, kwargs

    def fix_unit_registry(self, value: BaseQuantity) -> ureg.Quantity:
        """Check if the UnitRegistry from settings is used. If not try to fix it but give a warning."""
        if value is None:
            return value

        if not isinstance(value, (BaseQuantity, self.ureg.Quantity)):
            raise ValueError("If provided, value must be a Quantity")

        if not isinstance(value, self.ureg.Quantity):
            warnings.warn(
                "Unit registry mismatch detected. It's advisable to use the same unit registry.",
                RuntimeWarning,
            )
            # Recreate the Quantity with the correct registry
            if self.field_type == DECIMAL_FIELD:
                return self.ureg.Quantity(Decimal(value.magnitude) * self.ureg(str(value.units)))
            return self.ureg.Quantity(value.magnitude, str(value.units))
        return value

    def convert_quantity_for_output(self, value: BaseQuantity) -> AsIs:
        """Convert a Quantity to a format that can be saved to the database."""
        if not isinstance(value, BaseQuantity):
            raise ValueError(
                f"value '{value}' for model field {self.get_attname()} in model {self.model._meta.label} "
                f"is type {type(value)}, not a Quantity."
            )

        check_matching_unit_dimension(
            self.ureg,
            self.default_unit,
            [
                str(value.units),
            ],
        )

        if self.field_type == INTEGER_FIELD:
            return AsIs(
                "(%s::decimal, %s::integer, '%s'::text)"  # pylint: disable=consider-using-f-string
                % (
                    get_base_unit_magnitude(value),
                    int(value.magnitude),
                    value.units,
                )
            )
        if self.field_type == BIG_INTEGER_FIELD:
            return AsIs(
                "(%s::decimal, %s::bigint, '%s'::text)"  # pylint: disable=consider-using-f-string
                % (
                    get_base_unit_magnitude(value),
                    int(value.magnitude),
                    value.units,
                )
            )

        return AsIs(
            "(%s::decimal, %s::decimal, '%s'::text)"  # pylint: disable=consider-using-f-string
            % (
                get_base_unit_magnitude(value),
                value.magnitude,
                value.units,
            )
        )

    def get_prep_value(self, value):
        """Converts Python objects to query values.

        see: https://docs.djangoproject.com/en/5.0/howto/custom-model-fields/#converting-python-objects-to-query-values
        """
        if value in (None, "", [], (), {}):
            return value

        if isinstance(value, (int, float)):
            value = self.ureg.Quantity(value * self.ureg(self.default_unit))

        # If a dictionary of values was passed in, convert to a Quantity
        if isinstance(value, dict) and is_decimal_or_int(value.get("magnitude")) and value.get("units") is not None:
            value = self.ureg.Quantity(str(value.get("magnitude") * value.get("units")))

        if self.field_type == DECIMAL_FIELD and isinstance(value, Decimal):
            value = self.ureg.Quantity(value * self.ureg(self.default_unit))

        # value may be a tuple of Quantity, for instance if using the `range` Lookup
        if isinstance(value, tuple):
            return [self.convert_quantity_for_output(item) for item in value]

        return self.convert_quantity_for_output(value)

    def get_db_prep_value(self, value, connection, prepared=False):  # pylint: disable=useless-parent-delegation
        """Converts value to a backend-specific value.

        See: https://docs.djangoproject.com/en/5.0/howto/custom-model-fields/#converting-query-values-to-database-values
        """
        return super().get_db_prep_value(value, connection, prepared)

    def from_db_value(self, value, expression, connection) -> Optional[BaseQuantity]:  # pylint: disable=unused-argument
        """Converts a value as returned by the database to a Python object. It is the reverse of get_prep_value().

        See: https://docs.djangoproject.com/en/5.0/howto/custom-model-fields/#converting-values-to-python-objects
        """
        if value is None:
            return value

        if isinstance(value, str):
            # Expecting database to return a tring like "(0.5669904625000001,20,ounce)"
            try:
                comparator, magnitude, units = value[1:-1].split(",")
                comparator = Decimal(comparator)
                magnitude = Decimal(magnitude) if self.field_type == DECIMAL_FIELD else int(magnitude)
                return self.ureg.Quantity(magnitude * getattr(self.ureg, units))
            except Exception as e:
                raise ValueError("Could not parse string from database") from e

        # If we're dealing with an int, float, or Decimal here, it's likely an aggregate from the comparator column.
        # We need to take the value, convert it to a Quantity using the base units, and return it.
        elif isinstance(value, (int, float, Decimal)):
            return self.ureg.Quantity(value * get_base_units(self.ureg, self.default_unit))

        # If we're dealing with a Quantity from the default registry, convert it to use the correct registry.
        elif isinstance(value, BaseQuantity):
            return (
                self.ureg.Quantity(Decimal(str(value.magnitude)) * getattr(self.ureg, value.units))
                if self.field_type == DECIMAL_FIELD
                else self.ureg.Quantity(value.magnitude * getattr(self.ureg, value.units))
            )

        raise ValueError(f"Could not parse value from database: {value}")

    def value_to_string(self, obj) -> str:
        """Converts obj to a string. Used to serialize the value of the field."""
        value = self.value_from_object(obj)

        return f"{value.magnitude} {value.units}"

    def to_python(self, value):
        """Converts the value into the correct Python object.

        It acts as the reverse of value_to_string(), and is also called in clean().

        to_python() is called by deserialization and during the clean() method used from forms.

        As a general rule, to_python() should deal gracefully with any of the following arguments:

        - An instance of the correct type
        - A string
        - None (if the field allows null=True)
        """

        if isinstance(value, str):
            if is_decimal_or_int(value):
                # A decimal or integer string
                value = (
                    self.ureg.Quantity(Decimal(value), self.default_unit)
                    if self.field_type == DECIMAL_FIELD
                    else self.ureg.Quantity(int(value), self.default_unit)
                )
            # If a string unit name was passed in, will default to `1 <Unit('default_unit')>`
            value = self.ureg.Quantity(value)

        if isinstance(value, (float, int)):
            value = (
                self.ureg.Quantity(Decimal(str(value)), self.default_unit)
                if self.field_type == DECIMAL_FIELD
                else self.ureg.Quantity(int(value), self.default_unit)
            )

        if isinstance(value, Decimal):  # For instance if a default Decimal value was used in a model
            value = (
                self.ureg.Quantity(value, self.default_unit)
                if self.field_type == DECIMAL_FIELD
                else self.ureg.Quantity(int(value), self.default_unit)
            )

        if isinstance(value, BaseQuantity):
            value = self.fix_unit_registry(value)

        return value

    def validate(self, value, model_instance):
        """
        Validate value and raise ValidationError if necessary. Subclasses
        should override this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        if self.choices is not None and value not in self.empty_values:
            for option_key, option_value in self.choices:
                if isinstance(option_value, (list, tuple)):
                    # This is an optgroup, so look inside the group for options.
                    for optgroup_key, optgroup_value in option_value:
                        if value == optgroup_key:
                            return
                elif value == option_key:
                    return
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )

        # If the value is not None or blank, check that the value is a Quantity
        print(f"value in validate: {value} of {type(value)}")
        if value is not None and not value in self.empty_values:
            if not isinstance(value, BaseQuantity):
                raise ValidationError(_("Value must be a Quantity."), code="invalid")

        if value is None and not self.null:
            raise ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise ValidationError(self.error_messages["blank"], code="blank")

    def clean(self, value, model_instance) -> BaseQuantity:
        """Convert the value's type and run validation.

        Validation errors from to_python() and validate() are propagated. Return correct value if no error is raised.

        This is a copy from django's implementation but modified so that validators are only checked against the
        magnitude as otherwise the default database validators will not fail because of comparison errors.
        """
        value = self.to_python(value)
        check_value = self.get_prep_value(value)
        self.validate(check_value, model_instance)
        self.run_validators(check_value)
        return value

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        """Return a form field for this model field."""
        defaults = {
            "form_class": self.form_field_class,
            "default_unit": self.default_unit,
            "unit_choices": self.unit_choices,
            "label": self.name.capitalize(),
        }
        if self.field_type in [INTEGER_FIELD, BIG_INTEGER_FIELD]:
            defaults["min_value"] = -1 * self.MAX_VAL - 1 if self.MAX_VAL is not None else None
            defaults["max_value"] = self.MAX_VAL
        if self.field_type == DECIMAL_FIELD:
            defaults["max_digits"] = getattr(self, "max_digits", None)
            defaults["decimal_places"] = getattr(self, "decimal_places", None)
        defaults.update(kwargs)
        return super().formfield(**defaults)


class IntegerPintField(BasePintField):
    """A Django Model Field that resolves to a pint Pint object."""

    description = _("A Django Model Field that resolves to an Integer-based pint Pint object.")
    field_type = INTEGER_FIELD
    MAX_VAL = 2147483647
    FIELD_NAME = "IntegerField"


class BigIntegerPintField(BasePintField):
    """A Django Model Field that resolves to a pint Pint object with a larger max value."""

    description = _("A Django Model Field that resolves to a BigInteger-based pint Pint object.")
    field_type = BIG_INTEGER_FIELD
    MAX_VAL = 9223372036854775807
    FIELD_NAME = "BigIntegerField"


class DecimalPintField(BasePintField):
    """A Django Model Field that resolves to a pint Pint object with a decimal value."""

    description = _("A Django Model Field that resolves to a Decimal-based pint Pint object.")
    field_type = DECIMAL_FIELD
    name: str
    validate: Callable
    run_validators: Callable
    form_field_class = DecimalPintFormField

    def __init__(
        self,
        *args,
        decimal_places: int,
        max_digits: int,
        rounding_method: Optional[str] = None,
        **kwargs,
    ):
        """Initialize a Pint field.

        :param decimal_places: Number of decimal places to store
        :param max_digits: Total number of digits to store
        :param rounding_method: Rounding method to use
        """

        self.decimal_places = decimal_places
        self.max_digits = max_digits
        self.rounding_method = rounding_method

        # To be helpful, if there are missing argument we throw an error early
        if not isinstance(self.max_digits, int) or not isinstance(self.decimal_places, int):
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField. "
                    "max_digits and decimal_places must be provided as integers. "
                    f"{self.max_digits=}, {self.decimal_places=}."
                )
            )
        # and we also check that the valuesare sane
        if self.decimal_places < 0 or self.max_digits < 1 or self.decimal_places > self.max_digits:
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField. "
                    "max_digits and decimal_places need to positive, and max_digits "
                    "needs to be larger than decimal_places and at least 1. "
                    f"{self.max_digits=} and {self.decimal_places=} "
                    "are not valid parameters."
                )
            )

        # Borrowed from DRF's DecimalField
        if self.rounding_method is not None:  # ToDo: Check if we're doing the following correctly
            valid_rounding_methods = [v for k, v in vars(decimal).items() if k.startswith("ROUND_")]
            if not self.rounding_method in valid_rounding_methods:
                raise ValueError(
                    _(
                        "Invalid rounding_method option {self.rounding_method}. "
                        "If provided, rounding_method must be one of: {valid_rounding_methods}"
                    )
                )

        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)

        # If the value is not None or blank, check that the magnitude is a Decimal
        if value is not None and not value in self.empty_values:
            if not isinstance(value.magnitude, Decimal):
                raise ValidationError(_("Magnitude must be a Decimal."), code="invalid")

    def get_db_prep_save(self, value, connection) -> Decimal:  # pylint: disable=unused-argument
        """Get value that shall be saved to database, make sure it is transformed correctly."""

        if value is None:
            return value

        # If a dictionary of values was passed in, convert to a Quantity
        if isinstance(value, dict) and is_decimal_or_int(value.get("magnitude")) and value.get("units") is not None:
            value = self.ureg.Quantity(Decimal(value.get("magnitude")) * self.ureg(str(value.get("units"))))

        elif value and isinstance(value, BaseQuantity):
            quantizing_string = get_quantizing_string(max_digits=self.max_digits, decimal_places=self.decimal_places)

            new_magnitude = value.magnitude
            # Make sure magnitude is a decimal value. If it is an int, convert it
            if isinstance(new_magnitude, int):
                new_magnitude = Decimal(str(new_magnitude))
            if isinstance(new_magnitude, str):
                new_magnitude = Decimal(new_magnitude)
            new_magnitude = new_magnitude.quantize(Decimal(quantizing_string))

            value = self.ureg.Quantity(new_magnitude * getattr(self.ureg, str(value.units)))

        elif not isinstance(value, self.ureg.Quantity):
            raise ValueError(f"Could not parse value to save to database: {value}")

        python_obj = self.to_python(value)

        converted_python_obj = self.get_prep_value(python_obj)

        return converted_python_obj
