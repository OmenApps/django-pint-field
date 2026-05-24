"""Django admin integration for django_pint_field.

Provides a configurable list filter that buckets a Pint field into named
ranges using the field's base-unit comparator lookups.
"""

from __future__ import annotations

from django.contrib import admin


class PintComparatorRangeListFilter(admin.SimpleListFilter):
    """Admin list filter offering developer-defined Quantity ranges.

    Subclass and set ``parameter_name``, ``title``, ``field_name`` and
    ``ranges`` (a list of ``(label, low_quantity_or_None, high_quantity_or_None)``).
    Bounds are inclusive lower / exclusive upper, compared across units.
    """

    field_name: str = ""
    ranges: list[tuple[str, object, object]] = []

    def lookups(self, request, model_admin):
        """Return one ``(value, label)`` pair per configured range."""
        return [(label, label) for label, _low, _high in self.ranges]

    def queryset(self, request, queryset):
        """Filter the queryset by the selected range's bounds."""
        selected = self.value()
        if selected is None:
            return queryset
        for label, low, high in self.ranges:
            if label != selected:
                continue
            if low is not None:
                queryset = queryset.filter(**{f"{self.field_name}__gte": low})
            if high is not None:
                queryset = queryset.filter(**{f"{self.field_name}__lt": high})
            return queryset
        return queryset
