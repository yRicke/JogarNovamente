import threading
import math
import unittest
from unittest.mock import Mock, patch

from windows_io import XboxPad


class XboxPadTests(unittest.TestCase):
    def setUp(self):
        # Testa o adaptador sem conectar um controle nem gerar entradas reais.
        self.pad = XboxPad.__new__(XboxPad)
        self.device = Mock()
        self.pad._pad = self.device
        self.pad._button = 0x8000

    def test_y_is_released_when_stop_happens_during_press(self):
        stop = threading.Event()
        self.device.press_button.side_effect = lambda **kwargs: stop.set()
        self.assertTrue(self.pad.tap_y(stop))
        self.device.release_button.assert_called_once_with(button=0x8000)
        self.assertEqual(self.device.update.call_count, 2)

    def test_y_is_released_even_if_update_fails(self):
        self.device.update.side_effect = [RuntimeError("falha"), None]
        with self.assertRaises(RuntimeError):
            self.pad.tap_y(threading.Event())
        self.device.release_button.assert_called_once_with(button=0x8000)

    def test_cancelled_tap_never_presses(self):
        stop = threading.Event()
        stop.set()
        self.assertFalse(self.pad.tap_y(stop))
        self.device.press_button.assert_not_called()

    def test_close_neutralizes_and_disconnects(self):
        self.pad.close()
        self.device.reset.assert_called_once()
        self.device.update.assert_called_once()
        self.assertIsNone(self.pad._pad)

    def test_both_sticks_move_in_independent_directions_then_center(self):
        with patch("windows_io.random.uniform", side_effect=[0, math.pi / 2, 0.25]), \
                patch("windows_io.time.monotonic", side_effect=[0, 1]):
            self.assertTrue(self.pad.move_sticks(threading.Event(), lambda: True))
        left = self.device.left_joystick_float.call_args.kwargs
        right = self.device.right_joystick_float.call_args.kwargs
        self.assertAlmostEqual(left["x_value_float"], 0.75)
        self.assertAlmostEqual(left["y_value_float"], 0)
        self.assertAlmostEqual(right["x_value_float"], 0)
        self.assertAlmostEqual(right["y_value_float"], 0.75)
        self.device.reset.assert_called_once()

    def test_sticks_center_when_stopped_during_movement(self):
        stop = threading.Event()
        self.device.update.side_effect = stop.set
        self.assertTrue(self.pad.move_sticks(stop, lambda: True))
        self.device.reset.assert_called_once()

    def test_sticks_center_when_game_loses_focus(self):
        focus = Mock(side_effect=[True, False])
        self.assertTrue(self.pad.move_sticks(threading.Event(), focus))
        self.device.reset.assert_called_once()

    def test_sticks_never_move_outside_game(self):
        self.assertFalse(self.pad.move_sticks(threading.Event(), lambda: False))
        self.device.update.assert_not_called()

    def test_sticks_center_even_if_update_fails(self):
        self.device.update.side_effect = [RuntimeError("falha"), None]
        with self.assertRaises(RuntimeError):
            self.pad.move_sticks(threading.Event(), lambda: True)
        self.device.reset.assert_called_once()


if __name__ == "__main__":
    unittest.main()
