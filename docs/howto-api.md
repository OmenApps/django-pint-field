# REST Framework and API Integration

django-pint-field provides serializer fields for Django REST Framework that handle serialization, deserialization, and validation of Pint quantities in your API endpoints.

## Serializer Fields

Three serializer field classes are available:

- **IntegerPintRestField** -- for use with `IntegerPintField`. Outputs a string like `"1 gram"` or, with `wrap=True`, `"Quantity(1 gram)"`.
- **DecimalPintRestField** -- for use with `DecimalPintField`. Outputs a string like `"1.5 gram"` or, with `wrap=True`, `"Quantity(1.5 gram)"`.
- **PintRestField** -- outputs a dictionary: `{"magnitude": 1.5, "units": "gram"}`.

The string-based fields give a compact, human-readable format. The dictionary-based field gives a structured format that front-end applications can parse without string manipulation.

## Basic Serializer Setup

Given a `WeightModel` with `weight` as an `IntegerPintField` and `precise_weight` as a `DecimalPintField`:

```python
from rest_framework import serializers
from django_pint_field.rest import IntegerPintRestField, DecimalPintRestField


class WeightSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField()
    precise_weight = DecimalPintRestField()

    class Meta:
        model = WeightModel
        fields = ["id", "name", "weight", "precise_weight"]
```

By default this produces string output:

```json
{
  "id": 1,
  "name": "Sample Weight",
  "weight": "1000 gram",
  "precise_weight": "1000.372 gram"
}
```

## Using the Wrapped Representation

Set `wrap=True` to wrap the string output with `Quantity()`:

```python
from rest_framework import serializers
from django_pint_field.rest import IntegerPintRestField, DecimalPintRestField


class WeightSerializer(serializers.ModelSerializer):
    weight = IntegerPintRestField(wrap=True)
    precise_weight = DecimalPintRestField(wrap=True)

    class Meta:
        model = WeightModel
        fields = ["id", "name", "weight", "precise_weight"]
```

Output:

```json
{
  "id": 1,
  "name": "Sample Weight",
  "weight": "Quantity(1000 gram)",
  "precise_weight": "Quantity(1000.372 gram)"
}
```

## Using Dictionary Format

`PintRestField` returns magnitude and units as separate keys, which can be easier to work with in client code:

```python
from rest_framework import serializers
from django_pint_field.rest import PintRestField


class WeightSerializer(serializers.ModelSerializer):
    weight = PintRestField()

    class Meta:
        model = WeightModel
        fields = ["id", "name", "weight"]
```

Output:

```json
{
  "id": 1,
  "name": "Sample Weight",
  "weight": {
    "magnitude": 1000,
    "units": "gram"
  }
}
```

## ViewSet Example

A complete ViewSet with a custom `convert` action that accepts a target unit as a query parameter:

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_pint_field.units import ureg


class WeightViewSet(viewsets.ModelViewSet):
    queryset = WeightModel.objects.all()
    serializer_class = WeightSerializer

    @action(detail=True, methods=["get"])
    def convert(self, request, pk=None):
        instance = self.get_object()
        unit = request.query_params.get("unit", "gram")

        try:
            converted = instance.weight.quantity.to(getattr(ureg, unit))
            return Response(
                {"original": str(instance.weight), "converted": str(converted)}
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)
```

Usage: `GET /api/weights/1/convert/?unit=kilogram`

## Custom Validation in Serializers

Override `validate_<field>` to add business rules. This example rejects weights over 1000 kg:

```python
from rest_framework import serializers
from django_pint_field.rest import DecimalPintRestField
from django_pint_field.units import ureg


class WeightSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField()

    class Meta:
        model = WeightModel
        fields = ["id", "name", "weight"]

    def validate_weight(self, value):
        kg_value = value.to(ureg.kilogram)
        if kg_value.magnitude > 1000:
            raise serializers.ValidationError("Weight cannot exceed 1000 kg")
        return value
```

## Unit Conversion in Serializers

Use `SerializerMethodField` to include the weight in additional units alongside the original value:

```python
from rest_framework import serializers
from django_pint_field.rest import DecimalPintRestField
from django_pint_field.units import ureg


class WeightSerializer(serializers.ModelSerializer):
    weight = DecimalPintRestField(wrap=True)
    weight_in_kg = serializers.SerializerMethodField()
    weight_in_lbs = serializers.SerializerMethodField()

    class Meta:
        model = WeightModel
        fields = [
            "id",
            "name",
            "weight",
            "weight_in_kg",
            "weight_in_lbs",
        ]

    def get_weight_in_kg(self, obj):
        if obj.weight:
            converted = obj.weight.kilogram
            return f"{converted.magnitude:.2f} kg"
        return None

    def get_weight_in_lbs(self, obj):
        if obj.weight:
            converted = obj.weight.pound
            return f"{converted.magnitude:.2f} lb"
        return None
```

Output:

```json
{
  "id": 1,
  "name": "Sample Weight",
  "weight": "Quantity(1000.00 gram)",
  "weight_in_kg": "1.00 kg",
  "weight_in_lbs": "2.20 lb"
}
```

## Error Handling

The serializer fields include built-in validation. Invalid input produces clear error messages:

- Invalid magnitude values raise a validation error.
- Undefined or unrecognized units raise a validation error.
- Incompatible unit conversions (e.g., meters to grams) raise a validation error.
- Missing required fields raise a validation error.

Example error responses:

```json
{ "weight": ["Invalid magnitude value."] }
```

```json
{ "weight": ["Invalid or undefined unit."] }
```

```json
{ "weight": ["Cannot convert from meters to grams"] }
```

## Choosing a Serialization Format

Use **`PintRestField`** (dictionary format) when:

- You need a structured, explicit format with separate magnitude and units keys.
- Your API clients expect consistent JSON structures they can parse without string splitting.
- You are building a front-end application that binds magnitude and unit to separate form controls.

Use **`IntegerPintRestField`** or **`DecimalPintRestField`** (string format) when:

- You want a compact, human-readable representation.
- String-based output is the convention for your API consumers.
- You are integrating with systems that already handle string-encoded quantities.

## Django Ninja

The example project includes Django Ninja integration. See [Example Project](example-project) for details on how PintFields work with Django Ninja serialization.

---

**See also:**

- [API Reference](reference) for the complete serializer field API
