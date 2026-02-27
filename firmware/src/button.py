# Thanks to Oscar Acena: https://github.com/oscaracena/pybuttons

import time
from machine import Pin, ADC

class BUTTON:
    '''
    MicoPython driver for buttons.
    Supports debouncing and triggers a callback for single, double, and long presses.

    Example:

    def press_handler(btn, pattern):
        print("button id {} ".format(btn.get_id()), end="")
        if pattern == button.BUTTON.SINGLE_PRESS:
            print("pressed.")
        elif pattern == button.BUTTON.DOUBLE_PRESS:
            print("double pressed.")
        elif pattern == button.BUTTON.LONG_PRESS:
            print("long pressed.")

    btn = button.BUTTON()
    btn.on_press(press_handler) \
        .on_double_press(press_handler) \
        .on_press_for(press_handler, 1000)

    while True:
        btn.read()

    '''
    LOW, HIGH = range(2)
    IDLE, PRESSING = range(2)
    SINGLE_PRESS, DOUBLE_PRESS, LONG_PRESS = range(3)

    def __init__(self, pin: int = 47, pullup: bool = True, button_logic: int = LOW):
        self._id = pin
        self._button_logic = button_logic
        self._last_loop = 0
        self._loop_interval = 20
        self._double_press_timeout = 300
        self._press_for_timeout = 3000

        self._prev_state = self.IDLE
        self._state = self.IDLE
        self._press_count = 0
        self._first_pressed_at = 0
        self._pressed_since = 0
        self._is_debouncing = False

        self._callbacks = {}

        self._pin = None
        self._pin = Pin(
            self._id, Pin.IN, Pin.PULL_UP if pullup else None)

    def on_press(self, cb):
        self._callbacks["press"] = cb
        return self

    def on_double_press(self, cb, timeout=300):
        self._callbacks["double_press"] = cb
        self._double_press_timeout = timeout
        return self

    def on_press_for(self, cb, timeout=3000):
        self._callbacks["press_for"] = cb
        self._press_for_timeout = timeout
        return self

    def update_state(self, state):
        self._prev_state = self._state
        self._state = state
        return self

    def read(self):
        cur_time = time.ticks_ms()
        if cur_time - self._last_loop >= self._loop_interval:
            self._last_loop = cur_time
            x = self._pin.value()
            if x == self._button_logic:
                self.update_state(self.PRESSING)
            else:
                self.update_state(self.IDLE)
            self.loop()

    def loop(self):
        cur_time = time.ticks_ms()
        if self._prev_state == self.IDLE and \
            self._state == self.PRESSING:
            self._is_debouncing = True
            return

        if self._press_count > 0 and \
            not ("double_press" in self._callbacks and \
                cur_time - self._first_pressed_at <= self._double_press_timeout) and \
            not ("press_for" in self._callbacks and \
                self._pressed_since != 0 and \
                self._state == self.PRESSING):

            press_cb = self._callbacks.get("press")
            if press_cb:
                press_cb(self, self.SINGLE_PRESS)
            self._press_count = 0
            self._first_pressed_at = 0

        if self._prev_state == self.PRESSING and \
            self._state == self.PRESSING:

            if self._is_debouncing:
                self._press_count += 1
                if self._first_pressed_at == 0:
                    self._first_pressed_at = cur_time
                if self._pressed_since == 0:
                    self._pressed_since = cur_time
                self._is_debouncing = False

            press_for_cb = self._callbacks.get("press_for")
            if press_for_cb and self._press_count > 0 and \
                cur_time - self._pressed_since >= self._press_for_timeout:

                press_for_cb(self, self.LONG_PRESS)
                self._press_count = 0
                self._first_pressed_at = 0
                self._pressed_since = 0
                return

            double_press_cb = self._callbacks.get("double_press")
            if double_press_cb and self._press_count > 1 and \
                cur_time - self._first_pressed_at <= self._double_press_timeout:

                double_press_cb(self, self.DOUBLE_PRESS)
                self._press_count = 0
                self._first_pressed_at = 0

        if self._prev_state == self.PRESSING and \
            self._state == self.IDLE:
            self._pressed_since = 0

    def get_id(self):
        return self._id

    def get_pin(self):
        return self.get_id()
