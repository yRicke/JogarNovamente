import threading
import unittest
from unittest.mock import Mock

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


if __name__ == "__main__":
    unittest.main()
