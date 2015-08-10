#!/usr/bin/python
from emu import *
from factor import *
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

    def test_distance(self):
        ans = [
            ((0, 0), (0, 0), 0),
            ((0, 0), (0, 1), 1),
            ((0, 0), (-1, 0), 1),
            ((0, 0), (2, 3), 5),
            ((2, -3), (4, 0), 5),
            ((0, 0), (2, 3), 5),
            ((0, 0), (-3, -2), 5),
        ]
        for cell1, cell2, answer in ans:
            self.assertEqual(Unit.distance(cell1, cell2), answer)
            self.assertEqual(Unit.distance(cell2, cell1), answer)

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

    def test_neigh(self):
        for cell in [(0, 0), (0, 1)]:
            self.assertEqual(list(Unit.neighbors(cell)), list(Unit.neighbors_old(cell)))

class TestStat(unittest.TestCase):
    def test_trivial(self):
        stat = Stat()
        stat.add(1)
        for i in range(101):
            self.assertEqual([1], stat.perc([i]))

        stat.add(2)
        self.assertEqual([1, 2], stat.perc([0, 100]))

        for i in range(3, 11):
            stat.add(i)

        for i in range(1, 11):
            self.assertEqual([i], stat.perc([i * 10]))

if __name__ == "__main__":
    unittest.main()
