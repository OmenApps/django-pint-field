from django import forms
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import formats
from django.utils.translation import gettext_lazy as _
import logging
import datetime
import typing
import warnings
from decimal import Decimal
from pint import Quantity
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast

from .helper import check_matching_unit_dimension
from .units import ureg
from .widgets import PintWidget
from . import get_IntegerPintDBField, integer_pint_field_adapter


logger = logging.getLogger("django_pint_field")



DJANGO_JSON_SERIALIZABLE_BASE = Union[None, bool, str, int, float, complex, datetime.datetime]
DJANGO_JSON_SERIALIZABLE = Union[Sequence[DJANGO_JSON_SERIALIZABLE_BASE], Dict[str, DJANGO_JSON_SERIALIZABLE_BASE]]
NUMBER_TYPE = Union[int, float, Decimal]


class PintFieldMixin(object):
    to_number_type: Callable[[Any], NUMBER_TYPE]

    # TODO: Move these stuff into an Protocol or anything
    #       better defining a Mixin
    value_from_object: Callable[[Any], Any]
    name: str
    validate: Callable
    run_validators: Callable

    """A Django Model Field that resolves to a pint Pint object"""

    def __init__(
        self,
        default_unit: str,
        *args,
        unit_choices: Optional[typing.Iterable[str]] = None,
        **kwargs,
    ):
        """
        Create a Pint field
        :param default_unit: Unit description of base unit
        :param unit_choices: If given the possible unit choices with the same
                             dimension like the base_unit
        """
        if not isinstance(default_unit, str):
            raise ValueError('PintField must be defined with base units, eg: "gram"')

        self.ureg = ureg

        # we do this as a way of raising an exception if some crazy unit was supplied.
        unit = getattr(self.ureg, default_unit)  # noqa: F841

        # if we've not hit an exception here, we should be all good
        self.default_unit = default_unit

        if unit_choices is None:
            self.unit_choices: List[str] = [self.default_unit]
        else:
            self.unit_choices = list(unit_choices)
            # The multi widget expects that the base unit is always present as unit
            # choice.
            # Otherwise we would need to handle special cases for no good reason.
            if self.default_unit in self.unit_choices:
                self.unit_choices.remove(self.default_unit)
            # Base unit has to be the first choice, always as all values are saved as
            # base unit within the database and this would be the first unit shown
            # in the widget
            self.unit_choices = [self.default_unit, *self.unit_choices]

        # Check if all unit_choices are valid
        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

        super().__init__(*args, **kwargs)

    @property
    def units(self) -> str:
        return self.default_unit

    def deconstruct(
        self,
    ) -> Tuple[str, str, Sequence[DJANGO_JSON_SERIALIZABLE], Dict[str, DJANGO_JSON_SERIALIZABLE],]:
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
        super_deconstruct = getattr(super(), "deconstruct", None)
        if not callable(super_deconstruct):
            raise NotImplementedError("Tried to use Mixin on a class that has no deconstruct function. ")
        name, path, args, kwargs = super_deconstruct()
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
                    "quantityfield. "
                    "We assume the naming is equal but best use the same register as"
                    " for creating the quantityfield.",
                    RuntimeWarning,
                )
                return value.magnitude * self.ureg(str(value.units))
            else:
                return value
        else:
            raise ValueError(f"Value '{value}' ({type(value)} is not a quantity.")

    def get_prep_value(self, value: Any) -> Optional[NUMBER_TYPE]:
        """
        Perform preliminary non-db specific value checks and conversions.

        Make sure that we compare/use only values without a unit
        """
        # we store the value in the base units defined for this field
        if value is None:
            return None

        if isinstance(value, Quantity):
            quantity = self.fix_unit_registry(value)
            magnitude = quantity.to(self.default_unit).magnitude
        else:
            magnitude = value

        try:
            return self.to_number_type(magnitude)
        except (TypeError, ValueError) as e:
            raise e.__class__(
                "Field '%s' expected a number but got %r." % (self.name, value),
            ) from e

    def value_to_string(self, obj) -> str:
        value = self.value_from_object(obj)
        return str(self.get_prep_value(value))

    def from_db_value(self, value: Any, *args, **kwargs) -> Optional[Quantity]:
        if value is None:
            return None
        return self.ureg.Quantity(value * getattr(self.ureg, self.default_unit))

    def to_python(self, value) -> Optional[Quantity]:
        if isinstance(value, Quantity):
            return self.fix_unit_registry(value)

        if value is None:
            return None

        to_number = getattr(super(), "to_python")
        if not callable(to_number):
            raise NotImplementedError("Mixin not used with a class that has to_python function")

        value = cast(NUMBER_TYPE, to_number(value))

        return self.ureg.Quantity(value * getattr(self.ureg, self.default_unit))

    def clean(self, value, model_instance) -> Quantity:
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.

        This is a copy from djangos implementation but modified so that validators
        are only checked against the magnitude as otherwise the default database
        validators will not fail because of comparison errors
        """
        value = self.to_python(value)
        check_value = self.get_prep_value(value)
        self.validate(check_value, model_instance)
        self.run_validators(check_value)
        return value

    # TODO: Add tests, understand, add super call if required
    """
    # This code is untested and not documented. It also does not call the super method
    Therefore it is commented out for the moment (even so it is likely required)

    def get_prep_lookup(self, lookup_type, value):

        if lookup_type in ["lt", "gt", "lte", "gte"]:
            if isinstance(value, self.ureg.Quantity):
                v = value.to(self.default_unit)
                return v.magnitude
            return value
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": self.form_field_class,
            "default_unit": self.default_unit,
            "unit_choices": self.unit_choices,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class PintFormFieldMixin(object):
    """This formfield allows a user to choose which units they
    wish to use to enter a value, but the value is yielded in
    the default_unit
    """

    to_number_type: Callable[[Any], NUMBER_TYPE]

    # TODO: Move these stuff into an Protocol or anything
    #       better defining a Mixin
    validate: Callable
    run_validators: Callable
    error_messages: Dict[str, str]
    empty_values: Sequence[Any]
    localize: bool

    def __init__(self, *args, **kwargs):
        self.ureg = ureg
        self.default_unit = kwargs.pop("default_unit", None)
        if self.default_unit is None:
            raise ValueError("PintFormField requires a default_unit kwarg of a " "single unit type (eg: grams)")
        self.units = kwargs.pop("unit_choices", [self.default_unit])
        if self.default_unit not in self.units:
            self.units.append(self.default_unit)

        check_matching_unit_dimension(self.ureg, self.default_unit, self.units)

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
            return getattr(widget, "__name__") in classes_to_ignore

        widget = kwargs.get("widget", None)
        if widget is None or is_special_admin_widget(widget):
            widget = PintWidget(default_unit=self.default_unit, unit_choices=self.units)
        kwargs["widget"] = widget
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, Quantity):
            return value.to(self.default_unit)
        else:
            return value

    def clean(self, value):
        """
        General idea, first try to extract the correct number like done in the other
        classes and then follow the same procedure as in the django default field
        """
        if isinstance(value, list) or isinstance(value, tuple):
            val = value[0]
            units = value[1]
        else:
            # If no multi widget is used
            val = value
            units = self.default_unit

        if val in self.empty_values:
            # Make sure the correct functions are called also in case of empty values
            self.validate(None)
            self.run_validators(None)
            return None

        if units not in self.units:
            raise ValidationError(_("%(units)s is not a valid choice") % locals())

        if self.localize:
            val = formats.sanitize_separators(value)

        try:
            val = self.to_number_type(val)
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages["invalid"], code="invalid")

        val = self.ureg.Quantity(val * getattr(self.ureg, units)).to(self.default_unit)
        self.validate(val.magnitude)
        self.run_validators(val.magnitude)
        return val


class PintFormField(PintFormFieldMixin, forms.FloatField):
    to_number_type = float


class PintField(PintFieldMixin, models.FloatField):
    form_field_class = PintFormField
    to_number_type = float


class IntegerPintFormField(PintFormFieldMixin, forms.IntegerField):
    to_number_type = int


class IntegerPintField(PintFieldMixin, models.IntegerField):
    form_field_class = IntegerPintFormField
    to_number_type = int


class BigIntegerPintField(PintFieldMixin, models.BigIntegerField):
    form_field_class = IntegerPintFormField
    to_number_type = int


class PositiveIntegerPintField(PintFieldMixin, models.PositiveIntegerField):
    form_field_class = IntegerPintFormField
    to_number_type = int


class DecimalPintFormField(PintFormFieldMixin, forms.DecimalField):
    to_number_type = Decimal


class DecimalPintField(PintFieldMixin, models.DecimalField):
    form_field_class = DecimalPintFormField
    to_number_type = Decimal

    def __init__(
        self,
        default_unit: str,
        *args,
        unit_choices: Optional[List[str]] = None,
        verbose_name: str = None,
        name: str = None,
        max_digits: int = None,
        decimal_places: int = None,
        **kwargs,
    ):
        # We try to be friendly as default django, if there are missing argument
        # we throw an error early
        if not isinstance(max_digits, int) or not isinstance(decimal_places, int):
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField! "
                    "We expect max_digits and decimal_places to be set as integers."
                )
            )
        # and we also check the values to be sane
        if decimal_places < 0 or max_digits < 1 or decimal_places > max_digits:
            raise ValueError(
                _(
                    "Invalid initialization for DecimalPintField! "
                    "max_digits and decimal_places need to positive and max_digits"
                    "needs to be larger than decimal_places and at least 1. "
                    "So max_digits=%(max_digits)s and "
                    "decimal_plactes=%(decimal_places)s "
                    "are not valid parameters."
                )
                % locals()
            )

        super().__init__(
            default_unit,
            *args,
            unit_choices=unit_choices,
            verbose_name=verbose_name,
            name=name,
            max_digits=max_digits,
            decimal_places=decimal_places,
            **kwargs,
        )

    def get_db_prep_save(self, value, connection) -> Decimal:
        """
        Get Value that shall be saved to database, make sure it is transformed
        """
        converted = self.to_python(value)
        magnitude = self.get_prep_value(converted)
        return connection.ops.adapt_decimalfield_value(magnitude, self.max_digits, self.decimal_places)


class XYZPintFormField(forms.Field):
    """
    This formfield allows a user to choose which unit they wish to use to enter a value,
    which is saved to the composite field
    """

    to_number_type: Callable[[Any], NUMBER_TYPE]

    # TODO: Move this stuff into an Protocol or anything better defining a Mixin
    validate: Callable
    run_validators: Callable
    error_messages: Dict[str, str]
    empty_values: Sequence[Any]
    localize: bool

    def __init__(self, *args, **kwargs):
        self.ureg = ureg
        self.default_unit = kwargs.pop("default_unit", None)
        if self.default_unit is None:
            raise ValueError("PintFormField requires a default_unit kwarg of a single unit type (eg: grams)")
        self.unit_choices = kwargs.pop("unit_choices", [self.default_unit])
        if self.default_unit not in self.unit_choices:
            self.unit_choices.append(self.default_unit)

        check_matching_unit_dimension(self.ureg, self.default_unit, self.unit_choices)

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
            return getattr(widget, "__name__") in classes_to_ignore

        widget = kwargs.get("widget", None)
        if widget is None or is_special_admin_widget(widget):
            widget = PintWidget(default_unit=self.default_unit, unit_choices=self.unit_choices)
        kwargs["widget"] = widget
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        # if isinstance(value, Quantity):
        #     return value.to(self.default_unit)
        # else:
        #     return value

        return value

    def to_python(self, value):
        """
        Return an ureg.Quantity python object from the input value
        """
        if not value:
            raise ValidationError(self.error_messages["no_value"], code="no_value")

        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["invalid_list"], code="invalid_list")

        return self.ureg.Quantity(value[0] * getattr(self.ureg, value[1]))

    def clean(self, value):
        """
        Validate the given value and return its "cleaned" value as an
        appropriate Python object. Raise ValidationError for any errors.
        """
        value = self.to_python(value)
        # value here is a Quantity object. e.g.: <Quantity(3, 'pound')>
        #self.validate(value)
        #self.run_validators(value)
        return value


class XYZPintField(models.Field):
    to_number_type: Callable[[Any], NUMBER_TYPE]

    # TODO: Move this stuff into an Protocol or anything
    #       better defining a Mixin
    # value_from_object: Callable[[Any], Any]
    name: str
    validate: Callable
    run_validators: Callable
    form_field_class = XYZPintFormField

    """A Django Model Field that resolves to a pint Pint object"""

    def __init__(
        self,
        default_unit: str,
        *args,
        unit_choices: Optional[typing.Iterable[str]] = None,
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

        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return "integer_pint_field"

    # @property
    # def units(self) -> str:  # ToDo: Remove, since we should instead check self.value.units
    #     return self.default_unit

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
        # super_deconstruct = getattr(super(), "deconstruct", None)
        # if not callable(super_deconstruct):
        #     raise NotImplementedError("Tried to use Mixin on a class that has no deconstruct function. ")
        # name, path, args, kwargs = super_deconstruct()
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

    # def get_prep_value(self, value: Any):
    #     """
    #     value is the current value of the model’s attribute, and the method should return data in a format that has
    #     been prepared for use as a parameter in a query.

    #     see: https://docs.djangoproject.com/en/4.1/howto/custom-model-fields/#converting-python-objects-to-query-values
    #     """
    #     return integer_pint_field_adapter(value)

    def get_prep_value(self, value):
        IntegerPintDBField = get_IntegerPintDBField()
        return IntegerPintDBField(magnitude=int(value.magnitude), units=str(value.units))
        return (int(value.magnitude), str(value.units))

    # def get_db_prep_value(self, value, connection, prepared=False):
    #     """
    #     Do we need this???

    #     Some data types (for example, dates) need to be in a specific format before they can be used by a database backend.
    #     get_db_prep_value() is the method where those conversions should be made. The specific connection that will be used for
    #     the query is passed as the connection parameter. This allows you to use backend-specific conversion logic if it is required.
    #     """
    #     value = super().get_db_prep_value(value, connection, prepared)
    #     if value is not None:
    #         return integer_pint_field_adapter(value)
    #     return value

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

        print(f"from_db_value > value: {value}, type: {type(value)}")
        return self.ureg.Quantity(value.magnitude * getattr(self.ureg, value.units))

    # def from_db_value(self, value, expression, connection):
    #     if value is None:
    #         return value
    #     IntegerPintDBField = get_IntegerPintDBField()
    #     return IntegerPintDBField(value.magnitude, value.units)

    def value_to_string(self, obj) -> str:
        """
        Converts obj to a string. Used to serialize the value of the field.
        """
        value = self.value_from_object(obj)

        # ToDo: If using decimal, we need to sericlaize and deserialize in a manner that preserves the decimal
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
            logger.debug(f"to_python > isinstance(value, Quantity) - value = {value}")
            return self.fix_unit_registry(value)

        if isinstance(value, str):
            logger.debug(f"to_python > isinstance(value, str) - value = {value}")
            return self.ureg.Quantity(value)

        if value is None:
            return value

    # def to_python():
    #     IntegerPintDBField = get_IntegerPintDBField()
    #     if isinstance(value, IntegerPintDBField):
    #         return value  # returns integer_pint_field(magnitude, unit)

    #     if value is None:
    #         return value

    def clean(self, value, model_instance) -> Quantity:
        """
        Convert the value's type and run validation. Validation errors
        from to_python() and validate() are propagated. Return the correct
        value if no error is raised.

        This is a copy from djangos implementation but modified so that validators
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
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)
