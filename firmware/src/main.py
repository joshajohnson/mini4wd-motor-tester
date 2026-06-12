from machine import Pin, I2C
import time
from power_supply import PSU
from drv8837 import DRV8837
from motor_control import MotorControl
from tmp1075 import TMP1075
from pulse_counter import PulseCounter
from rotary_irq_esp import RotaryIRQ
from st7735_display import ST7735_display
from button import BUTTON
from ui import UI

time.sleep(3)  # Allow time to connect to REPL after a reset for debugging

# Init all the things
i2c = I2C(sda=Pin(8), scl=Pin(9))

display = ST7735_display()

led = Pin(0, Pin.OUT, Pin.PULL_DOWN)
# .on_double_press(press_handler) \
# .on_press_for(press_handler, 1000)

# Rotary encoder including button
rotary_enc = RotaryIRQ(pin_num_clk=45, pin_num_dt=48)
enc_btn = BUTTON(pin=47)

# Wheel RPM Sensor
wheel_sensor = PulseCounter(pin=1)

# Motor and related bits
psu = PSU(i2c, en_pin=16, dac_addr=0x60, imon_addr=0x40)
drv = DRV8837(motor_en=15, motor_in1=6, motor_in2=5)
tmp = TMP1075(i2c, addr=0x48)
rpm = PulseCounter(pin=2)

motor = MotorControl(psu, drv, rpm, tmp)

# Launch UI
app = UI(display)
app.show_menu(psu, motor, tmp, rotary_enc, enc_btn, wheel_sensor)
