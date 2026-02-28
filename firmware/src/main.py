from machine import Pin, I2C
import time


# Init I2C
i2c = I2C(sda=Pin(8), scl=Pin(9))

# Init misc GPIO
led = Pin(0, Pin.OUT, Pin.PULL_DOWN)




