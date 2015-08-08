#!/usr/bin/python
from emu import *
import unittest

class TestUnit(unittest.TestCase):
    def test_space(self):
        for x in range(-100, 100):
            for y in range(-100, 100):
                unit = Unit.field_to_unit_space((x, y))
                back = Unit.unit_to_field_space(unit)

                self.assertEqual(back, (x, y))

                field = Unit.unit_to_field_space((x, y))
                back = Unit.field_to_unit_space(field)

                self.assertEqual(back, (x, y))

        for x in range(1000):
            for y in (0, 1):
                self.assertEqual(Unit.field_to_unit_space((x, y)), (x, y))

        for x in range(1000):
            for y in (2, 3):
                self.assertEqual(Unit.field_to_unit_space((x, y)), (x - 1, y))

    def test_rot(self):
        cases = [
            [
                (2, 0),
                (0, 2),
                (-2, 2),
                (-2, 0),
                (0, -2),
                (2, -2),
                (2, 0)
            ],
            [
                (2, 1),
                (-1, 3),
                (-3, 2),
                (-2, -1),
                (1, -3),
                (3, -2),
                (2, 1)
            ]
        ]
        for circle in cases:
            for i in range(len(circle) - 1):
                self.assertEqual(Unit.rot60(circle[i]), circle[i + 1])

if __name__ == "__main__":
    unittest.main()
