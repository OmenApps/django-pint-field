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

### Changed

- Each `PintField` now reuses a single cached `PintFieldConverter`, avoiding a per-row allocation when loading querysets.

## [2024.11.1]

Major release with new features and improvements.

### Added

- TBD

[unreleased]: https://github.com/OmenApps/django-pint-field/compare/2024.11.1...HEAD
[2024.11.1]: https://github.com/OmenApps/django-pint-field/releases/tag/2024.11.1
