# Thanks to Matt Trentini: https://github.com/mattytrentini/micropython-tmp1075

from machine import I2C
from micropython import const

class TMP1075:

    '''
    MicroPython Driver for the TI TMP1075 temperature sensor.

    Example:

        i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))
        tmp1075 = TMP1075(i2c)
        tmp1075.get_temperature()

    See datasheet: http://www.ti.com/lit/ds/symlink/tmp1075.pdf
    
    '''

    REG_TEMP = const(0x00)
    REG_CONFIG = const(0x01)
    REG_LLIM = const(0x02)
    REG_HLIM = const(0x03)
    REG_DIEID = const(0x0F)

    def __init__(self, i2c=I2C, addr: int = 0x48):
        self.i2c = i2c
        self.addr = addr			  
        self._check_device()

    def _check_device(self):
        ''' Check comms, DIE ID should always be 0x7500 '''
        id = self.i2c.readfrom_mem(self.addr, self.REG_DIEID, 2)
        if (id[0] << 8 + id[1]) != 0x7500:
            raise ValueError(f'Incorrect DIE ID (got {hex((id[0] << 8) + id[1])}, expected 0x7500) or bad I2C comms')

    def get_temperature(self):
        ''' Get current temperature in degrees Celsius '''
        data = self.i2c.readfrom_mem(self.addr, self.REG_TEMP, 2)
        # 12-bit resolution, left-justified in 16 bits
        raw = (data[0] << 8) | data[1]
        raw = raw >> 4
        # Handle negative temperatures
        if raw & 0x800:
            raw -= 1 << 12
        # Convert to deg c
        temp = raw * 0.0625
        return temp

