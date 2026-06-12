from machine import Pin, Counter
import machine
import time
import collections


class PulseCounter:
    def __init__(self, pin: int = None):
        self.pin = Pin(pin, Pin.IN, None)

        self.pulse_count = 0
        self.window_start_ms = time.ticks_ms()
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._on_pulse)

        self.hz_samples_100ms = collections.deque((), 10)
        self.hz_samples_1s = collections.deque((), 10)
        self.hz_last_avg = (0.0, 0.0, 0.0)
        self.rpm_last_avg = (0.0, 0.0, 0.0)

    # Below is called every ISR
    def _on_pulse(self, pin):
        self.pulse_count += 1

    def update_pulse_count(self):
        """
        This function counts the IRQ triggered pulse count variable and updates the average variables
        """
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.window_start_ms)
        if elapsed >= 100:

            # Get the count over the last 100ms, reset the counter
            state = machine.disable_irq()
            count = self.pulse_count
            self.pulse_count = 0
            self.window_start_ms = now
            machine.enable_irq(state)

            # The 100ms average is the raw count over the last 100ms
            hz_avg_100ms = count * 10

            # The 1s average is using the 100ms average to keep the array size down
            self.hz_samples_1s.append(hz_avg_100ms)
            hz_avg_1s = sum(self.hz_samples_1s) / len(self.hz_samples_1s)

            self.hz_last_avg = (int(hz_avg_100ms), int(hz_avg_1s))
            self.rpm_last_avg = (hz_avg_100ms * 60, hz_avg_1s * 60)

    def get_hz_100ms(self):
        return int(self.hz_last_avg[0])

    def get_hz_1s(self):
        return int(self.hz_last_avg[1])

    def get_rpm_100ms(self):
        return int(self.rpm_last_avg[0])

    def get_rpm_1s(self):
        return int(self.rpm_last_avg[1])

    def get_state(self):
        return self.pin.value()
