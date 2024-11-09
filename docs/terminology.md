# Terminology and Definitions

Key terms and concepts used in django-pint-field.

## Basic Terms

### Physical Quantity

A physical quantity is a numerical measurement combined with a unit of measurement. For example, "5 meters" or "2.5 kilograms" are physical quantities.

### Unit

A unit is a standardized measurement of a physical property. For example, "meter" (length), "gram" (mass), or "second" (time) are units.

### Magnitude

The numeric value portion of a physical quantity. For example, in "5 meters", the magnitude is 5.

### Dimension

The type of physical property being measured. For example, length, mass, time, or temperature are dimensions. Units of the same dimension can be converted between each other (e.g., meters to feet), while units of different dimensions cannot (e.g., meters to kilograms).

## Field Components

### PintField

A Django model field that stores physical quantities in a composite type. It consists of three components:

- **comparator**: The magnitude in base units, used for database comparisons and calculations
- **magnitude**: The display magnitude in the user's chosen units
- **units**: The user's chosen units as a string

### Base Units

The standard units used internally for comparisons. For example, all lengths are converted to meters, all masses to kilograms, etc. Base units ensure accurate comparisons between quantities expressed in different but compatible units.

### Default Unit

The unit specified when defining a PintField. This unit is used as the default when no other unit is specified. Example: `weight = DecimalPintField(default_unit="gram")`.

### Unit Choices

An optional list of allowed units for a field. All units in this list must be compatible with the default unit (i.e., have the same dimension).

## Field Types

### DecimalPintField

A PintField that stores the magnitude as a decimal number with specified precision (max_digits and decimal_places).

### IntegerPintField

A PintField that stores the magnitude as an integer.

### BigIntegerPintField

A PintField that stores the magnitude as a big integer (for very large numbers).

## Indexes

### PintFieldComparatorIndex

A special index type for PintFields that indexes the comparator value, enabling efficient database queries across different units of the same dimension.

### Composite Type

A PostgreSQL database type that groups multiple related values together. Django-pint-field uses a composite type called 'pint_field' to store its three components (comparator, magnitude, and units).

## Other Terms

### Pint

The Python library used by django-pint-field for unit conversions and physical quantity handling. Pint provides the core functionality for unit parsing, conversion, and dimensional analysis.

### Unit Registry

A Pint object that defines all available units and their relationships. It can be customized to add new units or modify existing ones.

### Dimensionality

The set of base dimensions that make up a unit. For example, velocity has dimensionality of length/time, and acceleration has dimensionality of length/time².

### Compatible Units

Units that share the same dimensionality and can be converted between each other. For example, meters and feet are compatible (both are length), while meters and seconds are not.

### Unit Conversion

The process of converting a quantity from one unit to another compatible unit. For example, converting 1000 meters to kilometers or 2.2 pounds to kilograms.

### Composite Field Access

In PostgreSQL, the syntax for accessing components of a composite type field. For example, `(measurement).comparator` accesses the comparator component of a PintField named "measurement".
