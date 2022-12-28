from django.test import TestCase

from pint import DimensionalityError

import quantityfield.fields as fields
import quantityfield.helper as helper
from quantityfield.units import ureg


class TestMatchingUnitDimensionsHelper(TestCase):
    def test_valid_choices(self):
        helper.check_matching_unit_dimension(ureg, "meter", ["mile", "foot", "cm"])

    def test_invalid_choices(self):
        with self.assertRaises(DimensionalityError):
            helper.check_matching_unit_dimension(
                ureg, "meter", ["mile", "foot", "cm", "kg"]
            )


class TestEdgeCases(TestCase):
    def test_fix_unit_registry(self):
        field = fields.IntegerQuantityField("meter")
        with self.assertRaises(ValueError):
            field.fix_unit_registry(1)

    def test_get_prep_value(self):
        field = fields.IntegerQuantityField("meter")
        with self.assertRaises(ValueError):
            field.get_prep_value("foobar")
