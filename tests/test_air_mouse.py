"""Unit tests for the AirMouseController."""

import unittest
from unittest.mock import MagicMock

from core.air_mouse import AirMouseController


class FakeMouse:
    def __init__(self):
        self.position = (0.0, 0.0)


class TestAirMouseController(unittest.TestCase):
    def test_mapping_and_clamping(self):
        mouse = FakeMouse()
        am = AirMouseController(
            smoothing=0.5,
            active_x_bounds=(0.20, 0.80),
            active_y_bounds=(0.20, 0.80),
            mouse_controller=mouse,
        )
        am._screen_width = 1000.0
        am._screen_height = 800.0

        # Exact center (0.50, 0.50) -> rel is 0.50 -> maps to (500.0, 400.0)
        res = am.update(0.50, 0.50)
        self.assertIsNotNone(res)
        self.assertAlmostEqual(mouse.position[0], 500.0, delta=1.0)
        self.assertAlmostEqual(mouse.position[1], 400.0, delta=1.0)

        # Clamping left/top below active bounds (0.05, 0.05) -> clamped to 0.0
        am.reset()
        am.update(0.05, 0.05)
        self.assertAlmostEqual(mouse.position[0], 0.0, delta=1.0)
        self.assertAlmostEqual(mouse.position[1], 0.0, delta=1.0)

        # Clamping right/bottom above active bounds (0.95, 0.95) -> clamped to 1.0 -> screen max
        am.reset()
        am.update(0.95, 0.95)
        self.assertAlmostEqual(mouse.position[0], 1000.0, delta=1.0)
        self.assertAlmostEqual(mouse.position[1], 800.0, delta=1.0)

    def test_smoothing_and_tremor_rejection(self):
        mouse = FakeMouse()
        am = AirMouseController(
            smoothing=0.30,
            min_cutoff=0.005,
            active_x_bounds=(0.0, 1.0),
            active_y_bounds=(0.0, 1.0),
            mouse_controller=mouse,
        )
        am._screen_width = 1000.0
        am._screen_height = 1000.0

        # First position
        am.update(0.50, 0.50)
        self.assertEqual(mouse.position, (500.0, 500.0))

        # Tiny tremor (< 0.005 * 1000 = 5 px)
        am.update(0.501, 0.501)
        self.assertEqual(mouse.position, (500.0, 500.0))

        # Distinct movement: smoothed towards target (600.0, 600.0)
        am.update(0.60, 0.60)
        self.assertGreater(mouse.position[0], 500.0)
        self.assertLess(mouse.position[0], 600.0)

    def test_reset_clears_history(self):
        mouse = FakeMouse()
        am = AirMouseController(mouse_controller=mouse)
        am.update(0.5, 0.5)
        self.assertIsNotNone(am._curr_x)
        am.reset()
        self.assertIsNone(am._curr_x)
        self.assertIsNone(am._curr_y)

    def test_deactivate_parks_cursor(self):
        mouse = FakeMouse()
        am = AirMouseController(mouse_controller=mouse)
        am._screen_width = 1920.0
        am._screen_height = 1080.0
        am.update(0.5, 0.5)
        self.assertIsNotNone(am._curr_x)

        am.deactivate(park_cursor=True)
        self.assertIsNone(am._curr_x)
        self.assertEqual(mouse.position, (1910.0, 1070.0))

    def test_handles_missing_mouse_controller_gracefully(self):
        am = AirMouseController(mouse_controller=None)
        am._mouse = None
        self.assertIsNone(am.update(0.5, 0.5))


if __name__ == "__main__":
    unittest.main()
