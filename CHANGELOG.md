# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- SQL-native query expressions `PintConvert`, `PintComparator`, and `PintMagnitude` for converting and accessing Pint field components directly in PostgreSQL.
- Analytics aggregates `PintPercentile` and `PintMedian`, plus the `pint_histogram()` queryset helper, all computed in PostgreSQL.
- Optional django-filter integration: `PintFieldFilter` and `PintFieldRangeFilter` (in `django_pint_field.filters`), and the admin `PintComparatorRangeListFilter` (in `django_pint_field.admin`).
- System checks `E001` (non-PostgreSQL backend) and `W001` (missing `pint_field` composite type), plus a `setup_pint_field` management command that creates and verifies the composite type.
- `py.typed` marker so type checkers and IDEs treat the package as typed.
- `PintWindow` expression (`django_pint_field.aggregates.PintWindow`) for unit-aware running totals and partitioned aggregates over Pint fields. A plain `django.db.models.Window` cannot carry a Pint aggregate's unit conversion; `PintWindow` runs it and returns a `PintFieldProxy` in the field's base unit (use the wrapped aggregate's `output_unit`, or `.quantity.to(...)`, to convert).

### Changed

- Each `PintField` now reuses a single cached `PintFieldConverter`, avoiding a per-row allocation when loading querysets.
### Breaking Changes

- Unit-bearing Pint aggregates (`PintSum`, `PintAvg`, `PintMax`, `PintMin`, `PintStdDev`, `PintVariance`, `PintPercentile`, `PintMedian`) now set `window_compatible = False`. Wrapping one in a bare `django.db.models.Window(...)` raises `ValueError` at construction time instead of silently returning a base-unit number wearing the wrong unit (a potentially large, silent numerical error). Migrate `Window(PintSum("field"), ...)` to `PintWindow(PintSum("field"), ...)`. `PintCount` is unaffected and continues to work inside a plain `Window`.

## [2024.11.1]

Major release with new features and improvements.

### Added

- TBD

[unreleased]: https://github.com/OmenApps/django-pint-field/compare/2024.11.1...HEAD
[2024.11.1]: https://github.com/OmenApps/django-pint-field/releases/tag/2024.11.1
