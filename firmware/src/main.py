from machine import Pin, I2C
from power_supply import PSU
from drv8837 import DRV8837
from motor_control import MotorControl
from tmp1075 import TMP1075

# Init I2C
i2c = I2C(sda=Pin(8), scl=Pin(9))

# # Init misc GPIO
# led = Pin(0, Pin.OUT, Pin.PULL_DOWN)

psu = PSU(i2c, en_pin=16, dac_addr=0x60, imon_addr=0x40)
drv = DRV8837(motor_en=15, motor_in1=6, motor_in2=5)
tmp = TMP1075(i2c, addr=0x48)

motor = MotorControl(psu, drv, None, tmp)

def set_motor(mode, volatge):
    motor.set_state(mode, volatge)
    while True:
        motor.update_state()
        motor.update_current()
        # motor.update_rpm()
        print(f'State - Actual: {motor.motor_direction} Target: {motor.target_motor_direction} Voltage - Actual: {round(motor.voltage_mv/1000,2)}V Voltage: {round(motor.target_voltage_mv/1000, 2)}V Current 100ms: {round(motor.get_current_100ms(),3)}A Current 1s: {round(motor.get_current_1s(),3)}A Temp: {round(motor.get_temp(),1)}C')