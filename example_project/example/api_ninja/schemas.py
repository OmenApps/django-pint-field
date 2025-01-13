"""Schemas for the django-ninja API."""
from typing import Any

from ninja import Schema


class WeightBase(Schema):
    """Base schema for weight fields."""

    id: int
    weight: str  # Will be represented as string like "100 gram"

    @staticmethod
    def resolve_weight(obj: Any) -> str:
        """Convert Pint Quantity to string representation."""
        return str(obj.weight)


class IntegerWeight(WeightBase):
    """Schema for IntegerPintFieldSaveModel."""

    class Config:
        """Configuration for IntegerWeight."""
        model = "example.IntegerPintFieldSaveModel"


class BigIntegerWeight(WeightBase):
    """Schema for BigIntegerPintFieldSaveModel."""

    class Config:
        """Configuration for BigIntegerWeight."""
        model = "example.BigIntegerPintFieldSaveModel"


class DecimalWeight(WeightBase):
    """Schema for DecimalPintFieldSaveModel."""

    class Config:
        """Configuration for DecimalWeight."""
        model = "example.DecimalPintFieldSaveModel"
