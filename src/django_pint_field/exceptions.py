"""Custom exceptions for Django Pint Field."""

from django.core.exceptions import FieldError


class PintFieldLookupError(FieldError):
    """Used to alert about invalid lookups for Django Pint Fields."""
