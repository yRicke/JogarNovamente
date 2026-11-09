import threading
import unittest

from engine import Settings, run


class FakeStop:
    def __init__(self, clock, finish=1.6):
        self.clock = clock
        self.finish = finish
        self.cancelled = False

    def is_set(self):
        return self.cancelled or self.clock[0] >= self.finish

    def set(self):
        self.cancelled = True

    def wait(self, seconds):
        self.clock[0] = round(self.clock[0] + seconds, 5)
        return self.is_set()


class FakePad:
    def __init__(self, clock):
        self.clock = clock
        self.sent_at = []
        self.moved_at = []
        self.closed = False

    def tap_y(self, stop):
        self.sent_at.append(self.clock[0])
        return True

    def close(self):
        self.closed = True

    def move_sticks(self, stop, is_focused):
        self.moved_at.append(self.clock[0])
        return True


class EngineTests(unittest.TestCase):
    def exercise(self, focus=lambda now: True, simulate=False, finish=1.6, factory=None,
                 move_sticks=True):
        clock = [0.0]
        stop = FakeStop(clock, finish)
        pad = FakePad(clock)
        events = []
        run(Settings(0.5, 0.5, simulate, move_sticks), stop, lambda: focus(clock[0]),
            factory or (lambda: pad), lambda *event: events.append(event),
            clock=lambda: clock[0], choose_delay=lambda lo, hi: lo)
        return pad, events

    def test_first_command_waits_and_interval_is_respected(self):
        pad, events = self.exercise(focus=lambda now: True)
        self.assertEqual(pad.sent_at, [0.5, 1.0, 1.5])
        self.assertTrue(pad.closed)
        self.assertIn(("count", 3), events)

    def test_background_never_receives_commands(self):
        pad, _ = self.exercise(focus=lambda now: False)
        self.assertEqual(pad.sent_at, [])
        self.assertTrue(pad.closed)

    def test_returning_focus_restarts_full_wait(self):
        pad, _ = self.exercise(focus=lambda now: not 0.3 <= now < 0.8)
        self.assertEqual(pad.sent_at, [1.3])

    def test_focus_rechecked_at_moment_of_send(self):
        calls_at_due = 0

        def focus(now):
            nonlocal calls_at_due
            if now == 0.5:
                calls_at_due += 1
                return calls_at_due == 1
            return True

        pad, _ = self.exercise(focus=focus, finish=0.8)
        self.assertEqual(pad.sent_at, [])

    def test_simulation_does_not_create_pad_or_require_focus(self):
        def forbidden():
            self.fail("Simulação tentou criar um controle")

        pad, events = self.exercise(focus=lambda now: False, simulate=True, factory=forbidden)
        self.assertEqual(pad.sent_at, [])
        self.assertIn(("count", 3), events)

    def test_driver_error_is_reported_and_worker_finishes(self):
        def broken():
            raise RuntimeError("driver indisponível")

        _, events = self.exercise(factory=broken)
        self.assertEqual(events, [("error", "driver indisponível"), ("done", None)])

    def test_stop_interrupts_long_wait(self):
        stop = threading.Event()
        pad = FakePad([0])
        waiting = threading.Event()
        worker = threading.Thread(target=run, args=(
            Settings(3600, 3600), stop, lambda: True, lambda: pad,
            lambda kind, value: waiting.set() if kind == "status" else None))
        worker.start()
        try:
            self.assertTrue(waiting.wait(1))
        finally:
            stop.set()
            worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertTrue(pad.closed)
        self.assertEqual(pad.sent_at, [])

    def test_invalid_intervals(self):
        for minimum, maximum in [(0, 3), (10, 3), (3, 3601), (float("nan"), 10), (3, float("inf"))]:
            with self.subTest(minimum=minimum, maximum=maximum), self.assertRaises(ValueError):
                Settings(minimum, maximum)

    def test_sticks_move_occasionally_without_replacing_y(self):
        pad, events = self.exercise(finish=40.5)
        self.assertEqual(pad.moved_at, [20.0, 40.0])
        self.assertIn(("movements", 2), events)
        self.assertGreater(len(pad.sent_at), 70)

    def test_sticks_can_be_disabled(self):
        pad, events = self.exercise(finish=45, move_sticks=False)
        self.assertEqual(pad.moved_at, [])
        self.assertFalse(any(kind == "movements" for kind, _ in events))

    def test_sticks_wait_again_after_losing_focus(self):
        pad, _ = self.exercise(focus=lambda now: not 10 <= now < 11, finish=31.5)
        self.assertEqual(pad.moved_at, [31.0])

    def test_sticks_are_simulated_without_creating_pad(self):
        def forbidden():
            self.fail("Simulação tentou criar um controle")

        pad, events = self.exercise(simulate=True, finish=20.5, factory=forbidden)
        self.assertEqual(pad.moved_at, [])
        self.assertIn(("movements", 1), events)


if __name__ == "__main__":
    unittest.main()
