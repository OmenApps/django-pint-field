import logging
import typing
import warnings
from decimal import Decimal
from typing import Any, Callable, List, Optional

from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from pint import Quantity
from psycopg2.extensions import AsIs, adapt
from psycopg2.extras import register_composite

from .forms import DecimalPintFormField, IntegerPintFormField
from .helper import (
    check_matching_unit_dimension,
    get_base_unit_magnitude,
    get_base_units,
    get_quantizing_string,
    is_decimal_or_int,
)
from .units import ureg

logger = logging.getLogger("django_pint_field")


def integer_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::integer, %s::text)"
        % (
            comparator,
            magnitude,
            units,
        )
    )


def big_integer_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::bigint, %s::text)"
        % (
            comparator,
            magnitude,
            units,
        )
    )


def decimal_pint_field_adapter(value):
    comparator = adapt(value.comparator)
    magnitude = adapt(value.magnitude)
    units = adapt(str(value.units))
    return AsIs(
        "(%s::decimal, %s::decimal, %s::text)"
        % (
            comparator,
            magnitude,
            units,
        )
    )


class BasePintField(models.Field):
    to_number_type: int
    name: str
    validate: Callable
    run_validators: Callable
    form_field_class = IntegerPintFormField
    MAX_VAL = 2147483647
    FIELD_NAME = ""

    """A Django Model Field that resolves to a pint Pint object"""

    def __init__(
        self,
        default_unit: str,
        *args,
        unit_choices: Optional[typing.Iterable[str]] = None,
        verbose_name: str = None,
        name: str = None,
        **kwargs,
    ):
        """
        Create a Pint field
        :param default_unit: Unit description of default unit
        :param unit_choices: If given the possible unit choices with the same
                             dimension like the default_unit
        """
        if not isinstance(default_unit, str):
            raise ValueError('PintField must be defined with a default_unit, eg: "gram"')

        self.ureg = ureg

        # we do this as a way of raising an exception if some crazy unit was supplied.
        unit = getattr(self.ureg, default_unit)  # noqa: F841

        # if we've not hit an exception here, we should be all good
        self.default_unit = default_unit

        if unit_choices is None:
            self.unit_choices: List[str] = [self.default_unit]
        else:
            self.unit_choices = list(unit_choices)
            # Remove the default unit if present, since we will adjust its position later.
            if self.default_unit in self.unit_choices:
                self.unit_choices.remove(self.default_unit)

            # ToDo: Remove the selected unit if present, since we will adjust its position later.
            # if self.value.units in self.unit_choices:
            #    self.unit_choices.remove(self.value.units)

            # ToDo: If the model has been saved, the first unit in the select should be the saved unit
            # Default unit should be the first choice, always as all values are saved as
            # default unit within the database and this would be the first unit shown
            # in the widget
            self.unit_choices = [self.default_unit, *self.unit_choices]
            # ToDo: self.unit_choices = [self.value.units, self.default_unit, *self.unit_choices]

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

        super().__init__(default_unit, *args, **kwargs)

    def db_type(self, connection):
        return "integer_pint_field"

    def deconstruct(
        self,
    ):
        """
        Return enough information to recreate the field as a 4-tuple:

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

        return name, path, args, kwargs

    def fix_unit_registry(self, value: Quantity) -> Quantity:
        """
        Check if the UnitRegistry from settings is used.
        If not try to fix it but give a warning.
        """
        if isinstance(value, Quantity):
            if not isinstance(value, self.ureg.Quantity):
                # Could be fatal if different unit registers are used but we assume
                # the same is used within one project
                # As we warn for this behaviour, we assume that the programmer
                # will fix it and do not include more checks!
                warnings.warn(
                    "Trying to set value from a different unit register for "
                    "django_pint_field. "
                    "We assume the naming is equal but best use the same register as"
                    " for creating the django_pint_field.",
                    RuntimeWarning,
                )
                return value.magnitude * self.ureg(str(value.units))
            else:
                return value
        else:
            raise ValueError(f"Value '{value}' ({type(value)} is not a quantity.")

    def convert_quantity_for_output(self, quantity_item: Quantity):
        raise NotImplementedError("convert_quantity_for_output has not been implemented for this field")

    def get_prep_value(self, value):
        """
        value is the current value of the model’s attribute, and the method should return data in a format that has
        been prepared for use as a parameter in a query.

        see: https://docs.djangoproject.com/en/4.1/howto/custom-model-fields/#converting-python-objects-to-query-values
        """
        if value is None:
            return value

        # If a dictionary of values was passed in, convert to a Quantity
        if isinstance(value, dict) and is_decimal_or_int(value["magnitude"]) and value["units"] is not None:
            value = self.ureg.Quantity(str(value["magnitude"] * value["units"]))

        # value may be a tuple of Quantity, for instance if using the `range` Lookup

        if isinstance(value, tuple):
            return [self.convert_quantity_for_output(item) for item in value]

        return self.convert_quantity_for_output(value)

    def from_db_value(self, value: Any, *args, **kwargs):
        """
        Converts a value as returned by the database to a Python object. It is the reverse of get_prep_value().

        This method is not used for most built-in fields as the database backend already returns the correct Python type,
        or the backend itself does the conversion.

        expression is the same as self.


        If present for the field subclass, from_db_value() will be called in all circumstances when the data is loaded from
        the database, including in aggregates and values() calls.
        """
        if value is None:
            return value

        if not isinstance(value, Quantity):
            if isinstance(value, str):
                # Expecting database to return a tring like "(0.5669904625000001,20,ounce)"
                try:
                    comparator, magnitude, units = value[1:-1].split(",")
                    comparator = Decimal(comparator)
                    magnitude = int(magnitude)
                    return self.ureg.Quantity(magnitude * getattr(self.ureg, units))
                except:
                    raise Exception("Could not parse string from database")

            # If we're dealing with an int, float, or Decimal here, it's likely an aggregate from the comparator column.
            # We need to take the value, convert it to a Quantity using the base units, and return it.
            elif isinstance(value, (int, float, Decimal)):
                return self.ureg.Quantity(value * get_base_units(self.ureg, self.default_unit))

        return self.ureg.Quantity(value.magnitude * getattr(self.ureg, value.units))

    def value_to_string(self, obj) -> str:
        """
        Converts obj to a string. Used to serialize the value of the field.
        """
        value = self.value_from_object(obj)
        return str(value)

    def to_python(self, value):
        """
        Converts the value into the correct Python object. It acts as the reverse of value_to_string(), and is also called in clean().


        to_python() is called by deserialization and during the clean() method used from forms.

        As a general rule, to_python() should deal gracefully with any of the following arguments:

        An instance of the correct type (e.g., Hand in our ongoing example).
        A string
        None (if the field allows null=True)
        """

        if isinstance(value, Quantity):
            return self.fix_unit_registry(value)

        if isinstance(value, str):
            return self.ureg.Quantity(value)

        if isinstance(value, int):  # For instance if a default int value was used in a model
            return self.ureg.Quantity(value, self.default_unit)

        if value is None:
            return value

    def clean(self, value, model_instance) -> Quantity:
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.

        This is a copy from django's implementation but modified so that validators
        are only checked against the magnitude as otherwise the default database
        validators will not fail because of comparison errors
        """
        value = self.to_python(value)
        check_value = self.get_prep_value(value)
        self.validate(check_value, model_instance)
        self.run_validators(check_value)
        return value

    def formfield(self, **kwargs):
        defaults = {
            "form_class": self.form_field_class,
            "default_unit": self.default_unit,
            "unit_choices": self.unit_choices,
            "min_value": -self.MAX_VAL - 1,
            "max_value": self.MAX_VAL,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class IntegerPintField(BasePintField):
    MAX_VAL = 2147483647
    FIELD_NAME = "IntegerField"

    """A Django Model Field that resolves to a pint Pint object"""

    def db_type(self, connection):
        return "integer_pint_field"

    def convert_quantity_for_output(self, quantity_item: Quantity):
        if not isinstance(quantity_item, Quantity):
            raise ValueError("quantity_item must be a Quantity")

        check_matching_unit_dimension(
            self.ureg,
            self.default_unit,
            [
                str(quantity_item.units),
            ],
        )

        IntegerPintDBField = register_composite("integer_pint_field", connection.cursor().cursor, globally=True).type

        return integer_pint_field_adapter(
            IntegerPintDBField(
                comparator=get_base_unit_magnitude(quantity_item),
                magnitude=int(quantity_item.magnitude),
                units=str(quantity_item.units),
            )
        )


class BigIntegerPintField(BasePintField):
    MAX_VAL = 9223372036854775807
    FIELD_NAME = "BigIntegerField"

    """A Django Model Field that resolves to a pint Pint object"""

    def db_type(self, connection):
        return "big_integer_pint_field"

    def convert_quantity_for_output(self, quantity_item: Quantity):
        if not isinstance(quantity_item, Quantity):
            raise ValueError("quantity_item must be a Quantity")

        check_matching_unit_dimension(
            self.ureg,
            self.default_unit,
            [
                str(quantity_item.units),
            ],
        )

        BigIntegerPintDBField = register_composite(
            "big_integer_pint_field", connection.cursor().cursor, globally=True
        ).type
        return big_integer_pint_field_adapter(
            BigIntegerPintDBField(
                comparator=get_base_unit_magnitude(quantity_item),
                magnitude=int(quantity_item.magnitude),
                units=str(quantity_item.units),
            )
        )


class DecimalPintField(models.Field):
    to_number_type: Decimal
    name: str
    validate: Callable
    run_validators: Callable
    form_field_class = DecimalPintFormField

    """A Django Model Field that resolves to a pint Pint object"""

    def __init__(
        self,
        default_unit: str,
        *args,
        unit_choices: Optional[List[str]] = None,
        verbose_name: str = None,
        name: str = None,
        **kwargs,
    ):
        """
        Create a Pint field
        :param default_unit: Unit description of default unit
        :param unit_choices: If given the possible unit choices with the same
                             dimension like the default_unit
        """
        if not isinstance(default_unit, str):
            raise ValueError('PintField must be defined with a default_unit, eg: "gram"')

        self.ureg = ureg

        # we do this as a way of raising an exception if some crazy unit was supplied.
        unit = getattr(self.ureg, default_unit)  # noqa: F841

        # if we've not hit an exception here, we should be all good
        self.default_unit = default_unit

        if unit_choices is None:
            self.unit_choices: List[str] = [self.default_unit]
        else:
            self.unit_choices = list(unit_choices)
            # Remove the default unit if present, since we will adjust its position later.
            if self.default_unit in self.unit_choices:
                self.unit_choices.remove(self.default_unit)

            # ToDo: Remove the selected unit if present, since we will adjust its position later.
            # if self.value.units in self.unit_choices:
            #    self.unit_choices.remove(self.value.units)

            # ToDo: If the model has been saved, the first unit in the select should be the saved unit
            # Default unit should be the first choice, always as all values are saved as
            # default unit within the database and this would be the first unit shown
            # in the widget
            self.unit_choices = [self.default_unit, *self.unit_choices]
            # ToDo: self.unit_choices = [self.value.units, self.default_unit, *self.unit_choices]

        self.decimal_places = kwargs.pop("decimal_places", None)
        self.max_digits = kwargs.pop("max_digits", None)

        # We try to be friendly as default django, if there are missing argument
        # we throw an error early
        if not isinstance(self.max_digits, int) or not isinstance(self.decimal_places, int):
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField! "
                    "We expect max_digits and decimal_places to be set as integers. "
                    f"max_digits: {self.max_digits}, decimal_places: {self.decimal_places}."
                )
            )
        # and we also check the values to be sane
        if self.decimal_places < 0 or self.max_digits < 1 or self.decimal_places > self.max_digits:
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField! "
                    "max_digits and decimal_places need to positive and max_digits"
                    "needs to be larger than decimal_places and at least 1. "
                    f"So max_digits={self.max_digits} and "
                    f"decimal_plactes={self.decimal_places} "
                    "are not valid parameters."
                )
            )

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

        super().__init__(
            default_unit,
            *args,
            **kwargs,
        )

    def db_type(self, connection):
        return "decimal_pint_field"

    def deconstruct(
        self,
    ):
        """
        Return enough information to recreate the field as a 4-tuple:

         * The name of the field on the model, if contribute_to_class() has
           been run.
         * The import path of the field, including the class:e.g.
           django.db.models.DecimalField This should be the most portable
           version, so less specific may be better.
         * A list of positional arguments.
         * A dict of keyword arguments.

        """
        name, path, args, kwargs = super().deconstruct()
        kwargs["default_unit"] = self.default_unit
        kwargs["unit_choices"] = self.unit_choices
        kwargs["max_digits"] = self.max_digits
        kwargs["decimal_places"] = self.decimal_places

        return name, path, args, kwargs

    def fix_unit_registry(self, value: Quantity) -> Quantity:
        """
        Check if the UnitRegistry from settings is used.
        If not try to fix it but give a warning.
        """
        if isinstance(value, Quantity):
            if not isinstance(value, self.ureg.Quantity):
                # Could be fatal if different unit registers are used but we assume
                # the same is used within one project
                # As we warn for this behaviour, we assume that the programmer
                # will fix it and do not include more checks!
                warnings.warn(
                    "Trying to set value from a different unit register for "
                    "django_pint_field. "
                    "We assume the naming is equal but best use the same register as"
                    " for creating the django_pint_field.",
                    RuntimeWarning,
                )
                return self.ureg.Quantity(Decimal(value.magnitude) * self.ureg(str(value.units)))
            else:
                return value
        else:
            raise ValueError(f"Value '{value}' ({type(value)} is not a quantity.")

    def get_prep_value(self, value):
        """
        value is the current value of the model’s attribute, and the method should return data in a format that has
        been prepared for use as a parameter in a query.

        see: https://docs.djangoproject.com/en/4.1/howto/custom-model-fields/#converting-python-objects-to-query-values
        """

        def convert_quantity_for_output(quantity_item: Quantity):
            if not isinstance(quantity_item, Quantity):
                raise ValueError("quantity_item must be a Quantity")

            check_matching_unit_dimension(
                self.ureg,
                self.default_unit,
                [
                    str(quantity_item.units),
                ],
            )

            DecimalPintDBField = register_composite(
                "decimal_pint_field", connection.cursor().cursor, globally=True
            ).type

            return decimal_pint_field_adapter(
                DecimalPintDBField(
                    comparator=get_base_unit_magnitude(quantity_item),
                    magnitude=Decimal(str(quantity_item.magnitude)),
                    units=str(quantity_item.units),
                )
            )

        if value is None:
            return value

        # value may be a tuple of Quantity, for instance if using the `range` Lookup

        if isinstance(value, tuple):
            return [convert_quantity_for_output(item) for item in value]

        return convert_quantity_for_output(value)

    def get_db_prep_save(self, value, connection) -> Decimal:
        """
        Get Value that shall be saved to database, make sure it is transformed

        Some data types (for example, dates) need to be in a specific format before they can be used by a database backend.
        get_db_prep_value() is the method where those conversions should be made. The specific connection that will be used for
        the query is passed as the connection parameter. This allows you to use backend-specific conversion logic if it is required.
        """

        if value is None:
            return value

        # If a dictionary of values was passed in, convert to a Quantity
        if isinstance(value, dict) and is_decimal_or_int(value["magnitude"]) and value["units"] is not None:
            value = self.ureg.Quantity(Decimal(value["magnitude"]) * self.ureg(str(value["units"])))

        if value and isinstance(value, Quantity):
            quantizing_string = get_quantizing_string(max_digits=self.max_digits, decimal_places=self.decimal_places)

            new_magnitude = value.magnitude
            # Make sure magnitude is a decimal value. If it is an int, convert it
            if isinstance(new_magnitude, int):
                new_magnitude = Decimal(str(new_magnitude))
            if isinstance(new_magnitude, str):
                new_magnitude = Decimal(new_magnitude)
            new_magnitude = new_magnitude.quantize(Decimal(quantizing_string))

            value = self.ureg.Quantity(new_magnitude * getattr(self.ureg, str(value.units)))

        python_obj = self.to_python(value)

        converted_python_obj = self.get_prep_value(python_obj)

        return converted_python_obj

    def from_db_value(self, value: Any, *args, **kwargs):
        """
        Converts a value as returned by the database to a Python object. It is the reverse of get_prep_value().

        This method is not used for most built-in fields as the database backend already returns the correct Python type,
        or the backend itself does the conversion.

        expression is the same as self.


        If present for the field subclass, from_db_value() will be called in all circumstances when the data is loaded from
        the database, including in aggregates and values() calls.
        """
        if value is None:
            return value

        if not isinstance(value, Quantity):
            if isinstance(value, str):
                # Expecting database to return a tring like "(0.5669904625000001,20,ounce)"
                try:
                    comparator, magnitude, units = value[1:-1].split(",")
                    comparator = Decimal(comparator)
                    magnitude = Decimal(magnitude)

                    return self.ureg.Quantity(magnitude * getattr(self.ureg, units))
                except:
                    raise Exception("Could not parse string from database")

            # If we're dealing with something other than a Quantity here, it's likely an aggregate from the comparator column.
            # We need to take the value, convert it to a Quantity using the base units, and return it.
            if isinstance(value, (int, float, Decimal)):
                return self.ureg.Quantity(value * get_base_units(self.ureg, self.default_unit))

        return self.ureg.Quantity(Decimal(str(value.magnitude)) * getattr(self.ureg, value.units))

    def value_to_string(self, obj) -> str:
        """
        Converts obj to a string. Used to serialize the value of the field.
        """
        value = self.value_from_object(obj)

        # ToDo: If using decimal, we need to serialaize and deserialize in a manner that preserves the decimal
        return str(value)

    def to_python(self, value):
        """
        Converts the value into the correct Python object. It acts as the reverse of value_to_string(), and is also called in clean().


        to_python() is called by deserialization and during the clean() method used from forms.

        As a general rule, to_python() should deal gracefully with any of the following arguments:

        An instance of the correct type (e.g., Hand in our ongoing example).
        A string
        None (if the field allows null=True)
        """
        if isinstance(value, Quantity):
            return self.fix_unit_registry(value)

        if isinstance(value, str):
            return self.ureg.Quantity(value)

        if isinstance(value, Decimal):  # For instance if a default Decimal value was used in a model
            return self.ureg.Quantity(value, self.default_unit)

        if value is None:
            return value

    def clean(self, value, model_instance) -> Quantity:
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.

        This is a copy from django's implementation but modified so that validators
        are only checked against the magnitude as otherwise the default database
        validators will not fail because of comparison errors
        """

        value = self.to_python(value)
        check_value = self.get_prep_value(value)
        self.validate(check_value, model_instance)
        self.run_validators(check_value)
        return value

    def formfield(self, **kwargs):
        defaults = {
            "form_class": self.form_field_class,
            "max_digits": self.max_digits,
            "decimal_places": self.decimal_places,
            "default_unit": self.default_unit,
            "unit_choices": self.unit_choices,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
