# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2026.6.1]

### Fixed

- Attribute-style unit conversion (`obj.field.unit`, e.g. `product.weight.kilogram`) now works on unsaved/in-memory instances, not only on rows loaded from the database. The `PintField` descriptor was previously overwritten by the bare field instance, so an unsaved instance held a raw `Quantity` and `obj.field.kilogram` raised `AttributeError` until the row was saved and reloaded.
- Deferred loading of a Pint field via `.only()` / `.defer()` now lazily loads and returns the value instead of the field object (the descriptor now subclasses Django's `DeferredAttribute`).

### Changed

- Accessing a `PintField` on an unsaved instance (including the instance returned by `Model(...)` or `objects.create()`) now returns a `PintFieldProxy`, consistent with database-loaded instances. **Migration:** code that relied on getting a bare Pint `Quantity` from such instances should use `obj.field.quantity` for the raw `Quantity` (for example `obj.field.quantity.to("kg")` instead of `obj.field.to("kg")`), or the proxy shortcut `obj.field.kilogram`. Loaded instances are unaffected - they already returned a proxy.

## [2026.5.1] & [2026.5.2]

### Added

- SQL-native query expressions `PintConvert`, `PintComparator`, and `PintMagnitude` for converting and accessing Pint field components directly in PostgreSQL.
- Analytics aggregates `PintPercentile` and `PintMedian`, plus the `pint_histogram()` queryset helper, all computed in PostgreSQL.
- Optional django-filter integration: `PintFieldFilter` and `PintFieldRangeFilter` (in `django_pint_field.filters`), and the admin `PintComparatorRangeListFilter` (in `django_pint_field.admin`).
- System checks `E001` (non-PostgreSQL backend) and `W001` (missing `pint_field` composite type), plus a `setup_pint_field` management command that creates and verifies the composite type.
- `py.typed` marker so type checkers and IDEs treat the package as typed.
- `PintWindow` expression (`django_pint_field.aggregates.PintWindow`) for unit-aware running totals and partitioned aggregates over Pint fields. A plain `django.db.models.Window` cannot carry a Pint aggregate's unit conversion; `PintWindow` runs it and returns a `PintFieldProxy` in the field's base unit (use the wrapped aggregate's `output_unit`, or `.quantity.to(...)`, to convert).
- Support for `bulk_update()` of Pint fields, and expression-based `update()` via `Cast(Case(When(..., then=Value(Quantity(...)))), output_field=field)`.

### Changed

- Each `PintField` now reuses a single cached `PintFieldConverter`, avoiding a per-row allocation when loading querysets.
- Pint fields now pass resolved query expressions through `get_db_prep_save` (this is what enables `bulk_update`/`Case`/`When`), mirroring Django's base `Field` behavior. Unsupported arithmetic on the composite column (e.g. `F("field") - value`) now raises a clear `ValidationError` instead of failing with an opaque database operator error.

### Breaking Changes

- Unit-bearing Pint aggregates (`PintSum`, `PintAvg`, `PintMax`, `PintMin`, `PintStdDev`, `PintVariance`, `PintPercentile`, `PintMedian`) now set `window_compatible = False`. Wrapping one in a bare `django.db.models.Window(...)` raises `ValueError` at construction time instead of silently returning a base-unit number wearing the wrong unit (a potentially large, silent numerical error). Migrate `Window(PintSum("field"), ...)` to `PintWindow(PintSum("field"), ...)`. `PintCount` is unaffected and continues to work inside a plain `Window`.

## [2024.11.1]

Major release with new features and improvements.

### Added

- TBD

[unreleased]: https://github.com/OmenApps/django-pint-field/compare/2024.11.1...HEAD
[2024.11.1]: https://github.com/OmenApps/django-pint-field/releases/tag/2024.11.1
