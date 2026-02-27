import machine
import time

import button

# Init I2C
# i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))

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