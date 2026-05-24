"""SQL-native query expressions for django_pint_field.

These expressions read and transform the PostgreSQL composite ``pint_field``
type (components: ``comparator``, ``magnitude``, ``units``) directly in SQL,
so conversions and comparisons run set-based instead of in Python.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import DecimalField
from django.db.models import Func
from django.db.models import Value

from .units import ureg


Quantity = ureg.Quantity


class _PintComponentAccessor(Func):
    """Base for expressions exposing one component of the ``pint_field`` composite.

    Subclasses set ``component`` to the composite attribute to read
    (``"comparator"`` or ``"magnitude"``). A string argument is coerced to an
    ``F()`` reference by ``Func`` automatically.
    """

    output_field = DecimalField()
    arity = 1
    component = ""

    def as_sql(self, compiler, connection, **extra):
        """Compile to ``(<column>).<component>``."""
        sql, params = compiler.compile(self.source_expressions[0])
        return f"({sql}).{self.component}", params


class PintComparator(_PintComponentAccessor):
    """Expose the base-unit ``comparator`` component of a Pint field in SQL."""

    component = "comparator"


class PintMagnitude(_PintComponentAccessor):
    """Expose the original ``magnitude`` component of a Pint field in SQL."""

    component = "magnitude"


def _affine_constants(to_unit: str) -> tuple[Decimal, Decimal]:
    """Return (b, m) such that ``target = (comparator - b) / m``.

    ``comparator`` is stored in base units. For any unit (multiplicative or
    offset/affine), ``base = m * target + b`` where::

        b = Q(0, to_unit).to_base_units().magnitude
        m = Q(1, to_unit).to_base_units().magnitude - b

    Multiplicative units (gram, meter, …) yield b == 0; offset units
    (degC, degF) yield b != 0.
    """
    b = Decimal(str(Quantity(0, to_unit).to_base_units().magnitude))
    m = Decimal(str(Quantity(1, to_unit).to_base_units().magnitude)) - b
    return b, m


class PintConvert(Func):
    """Convert a Pint field to ``to_unit`` entirely in SQL.

    Usage::

        Model.objects.annotate(kg=PintConvert("weight", "kilogram"))
              .filter(kg__gte=2)
              .order_by("-kg")

    The annotation is a plain ``DecimalField`` holding the magnitude in
    ``to_unit`` - compare it against plain numbers, not ``Quantity`` objects.

    Notes:
        - ``to_unit`` must be dimensionally compatible with the field's
          ``default_unit``; an incompatible unit (e.g. converting a mass field
          to a length unit) raises ``ValidationError`` when the query is built.
        - For index-backed filtering, prefer a native field lookup against a
          ``Quantity`` (e.g. ``filter(weight__gte=Quantity(2, "kilogram"))``),
          which matches ``PintFieldComparatorIndex``. ``PintConvert`` is best
          used to project a converted magnitude; converting to a non-base unit
          wraps the comparator in arithmetic that the planner cannot match
          against the comparator index.
    """

    output_field = DecimalField()
    arity = 1

    def __init__(self, expression, to_unit: str, **extra):
        """Validate the unit and precompute affine constants at construction.

        Computing the constants here (rather than in ``as_sql``) makes an
        undefined or non-scalable ``to_unit`` fail fast at the point the
        expression is written, instead of deep inside query compilation.
        """
        if not isinstance(to_unit, str) or not to_unit.strip():
            raise ValueError("PintConvert requires a non-empty unit string for `to_unit`.")
        self.to_unit = to_unit
        self._b, self._m = _affine_constants(to_unit)
        if self._m == 0:
            raise ValueError(f"Cannot convert to non-scalable unit: {to_unit!r}")
        super().__init__(expression, **extra)

    def resolve_expression(self, *args, **kwargs):
        """Resolve, then verify ``to_unit`` matches the source field's dimension.

        The source field is only known once resolved, so dimensional
        compatibility is checked here (at query-build time) rather than in
        ``__init__``. Non-field sources (e.g. nested expressions) are skipped.
        """
        resolved = super().resolve_expression(*args, **kwargs)
        field = getattr(resolved.source_expressions[0], "field", None)
        default_unit = getattr(field, "default_unit", None)
        if default_unit is not None:
            expected = ureg.Unit(default_unit).dimensionality
            if ureg.Unit(self.to_unit).dimensionality != expected:
                raise ValidationError(
                    f"Cannot convert a field measured in '{default_unit}' to '{self.to_unit}': "
                    "incompatible dimensionality."
                )
        return resolved

    def as_sql(self, compiler, connection, **extra):
        """Compile to ``((<column>).comparator - b) / m``, dropping identity terms.

        When ``b == 0`` and ``m == 1`` (converting to the base unit) the
        expression collapses to the bare comparator, keeping it usable by
        ``PintFieldComparatorIndex``.
        """
        comparator_sql, params = compiler.compile(self.source_expressions[0])
        sql = f"({comparator_sql}).comparator"
        out_params = [*params]

        if self._b != 0:
            b_sql, b_params = compiler.compile(Value(self._b, output_field=DecimalField()))
            sql = f"({sql} - {b_sql})"
            out_params += [*b_params]

        if self._m != 1:
            m_sql, m_params = compiler.compile(Value(self._m, output_field=DecimalField()))
            sql = f"({sql}) / {m_sql}"
            out_params += [*m_params]

        return sql, out_params
