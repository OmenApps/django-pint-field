"""Adapters for converting to and from Quantity objects."""

import logging
from decimal import Decimal

from django.db import connection
from psycopg.adapt import Dumper
from psycopg.pq import Format
from psycopg.types.composite import TupleDumper

from .units import ureg


logger = logging.getLogger(__name__)

Quantity = ureg.Quantity


class PintDumper(Dumper):
    """Dumps Pint Quantity objects to PostgreSQL composite type."""

    format = Format.TEXT

    def dump(self, obj: Quantity) -> bytes:
        """Convert Quantity object to composite type data."""
        # Always store as Decimal in the database
        base_magnitude = Decimal(str(obj.to_base_units().magnitude))
        magnitude = Decimal(str(obj.magnitude))
        units = str(obj.units)

        data = (base_magnitude, magnitude, units)
        return TupleDumper(cls=Quantity, context=connection.connection).dump(data)
