from machine import Pin, I2C
from power_supply import PSU
from drv8837 import DRV8837
from motor_control import MotorControl
from tmp1075 import TMP1075
from pulse_counter import PulseCounter
from rotary_irq_esp import RotaryIRQ
from st7735_display import ST7735_display
from button import BUTTON

# Init I2C
i2c = I2C(sda=Pin(8), scl=Pin(9))

# Init Display
# display = ST7735_display()

# Init misc GPIO
led = Pin(0, Pin.OUT, Pin.PULL_DOWN)

def press_handler(btn, pattern):
    print("button id {} ".format(btn.get_id()), end="")
    if pattern == BUTTON.SINGLE_PRESS:
        print("pressed.")
    elif pattern == BUTTON.DOUBLE_PRESS:
        print("double pressed.")
    elif pattern == BUTTON.LONG_PRESS:
        print("long pressed.")
btn = BUTTON(pin = 47)
btn.on_press(press_handler) \
    .on_double_press(press_handler) \
    .on_press_for(press_handler, 1000)

rotary_enc = RotaryIRQ(pin_num_clk=45, pin_num_dt=48)

# Wheel RPM Sensor
wheel = PulseCounter(pin = 1)

# Motor and related bits
psu = PSU(i2c, en_pin=16, dac_addr=0x60, imon_addr=0x40)
drv = DRV8837(motor_en=15, motor_in1=6, motor_in2=5)
tmp = TMP1075(i2c, addr=0x48)
rpm = PulseCounter(pin=2)

motor = MotorControl(psu, drv, rpm, tmp)

def set_motor(mode, voltage):
    motor.set_state(mode, voltage)

def loop():
    enc_old = rotary_enc.value()
    while True:
        # Need to call the below to keep the motor state updated
        motor.update_state()
        motor.update_current()
        motor.update_rpm()

        # Keep wheel speed updated
        wheel.update_pulse_count()

        # Button and rotary encoder updates
        btn.read()

        enc_new = rotary_enc.value()
        if enc_old != enc_new:
            enc_old = enc_new
            print('result =', enc_new)

        print(f'State: {motor.motor_direction} Voltage: {round(motor.target_voltage_mv/1000, 2)}V Current 100ms: {round(motor.get_current_100ms(),3)}A Temp: {round(motor.get_temp(),1)}C RPM 100ms: {motor.get_rpm_100ms()} RPM 1s: {motor.get_rpm_1s()} Wheel 100ms: {wheel.get_rpm_100ms()} Wheel 1s: {wheel.get_rpm_1s()}')

