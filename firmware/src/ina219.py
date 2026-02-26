# The MIT License (MIT)
#
# Copyright (c) 2017 Dean Miller for Adafruit Industries
#
# Thanks to Robert Hammelrath: https://github.com/robert-hh/INA219/blob/master/ina219.py

from machine import I2C
from micropython import const

class INA219:
    '''
    MicroPython Driver for the TI INA219 current sensor.

    Example:

        i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))
        imon = INA219(i2c, addr=0x40)
        imon.get_voltage()
        imon.get_current()

    See datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf
    
    '''

    REG_CONFIG = const(0x00)
    REG_SHUNT = const(0x01)
    REG_BUS = const(0x02)
    REG_POWER = const(0x03)
    REG_CURRENT = const(0x04)
    REG_CAL = const(0x05)

    CONFIG_BVOLTAGERANGE_MASK = const(0x2000)  # Bus Voltage Range Mask
    CONFIG_BVOLTAGERANGE_16V = const(0x0000)  # 0-16V Range
    CONFIG_BVOLTAGERANGE_32V = const(0x2000)  # 0-32V Range

    CONFIG_GAIN_MASK = const(0x1800)     # Gain Mask
    CONFIG_GAIN_1_40MV = const(0x0000)   # Gain 1, 40mV Range
    CONFIG_GAIN_2_80MV = const(0x0800)   # Gain 2, 80mV Range
    CONFIG_GAIN_4_160MV = const(0x1000)  # Gain 4, 160mV Range
    CONFIG_GAIN_8_320MV = const(0x1800)  # Gain 8, 320mV Range

    CONFIG_BADCRES_MASK = const(0x0780)   # Bus ADC Resolution Mask
    CONFIG_BADCRES_9BIT = const(0x0080)   # 9-bit bus res = 0..511
    CONFIG_BADCRES_10BIT = const(0x0100)  # 10-bit bus res = 0..1023
    CONFIG_BADCRES_11BIT = const(0x0200)  # 11-bit bus res = 0..2047
    CONFIG_BADCRES_12BIT = const(0x0400)  # 12-bit bus res = 0..4097

    CONFIG_SADCRES_MASK = const(0x0078)              # Shunt ADC Res. &  Avg. Mask
    CONFIG_SADCRES_9BIT_1S_84US = const(0x0000)      # 1 x 9-bit shunt sample
    CONFIG_SADCRES_10BIT_1S_148US = const(0x0008)    # 1 x 10-bit shunt sample
    CONFIG_SADCRES_11BIT_1S_276US = const(0x0010)    # 1 x 11-bit shunt sample
    CONFIG_SADCRES_12BIT_1S_532US = const(0x0018)    # 1 x 12-bit shunt sample
    CONFIG_SADCRES_12BIT_2S_1060US = const(0x0048)   # 2 x 12-bit sample average
    CONFIG_SADCRES_12BIT_4S_2130US = const(0x0050)   # 4 x 12-bit sample average
    CONFIG_SADCRES_12BIT_8S_4260US = const(0x0058)   # 8 x 12-bit sample average
    CONFIG_SADCRES_12BIT_16S_8510US = const(0x0060)  # 16 x 12-bit sample average
    CONFIG_SADCRES_12BIT_32S_17MS = const(0x0068)    # 32 x 12-bit sample average
    CONFIG_SADCRES_12BIT_64S_34MS = const(0x0070)    # 64 x 12-bit sample average
    CONFIG_SADCRES_12BIT_128S_69MS = const(0x0078)   # 128 x 12-bit sample average

    CONFIG_MODE_MASK = const(0x0007)  # Operating Mode Mask
    CONFIG_MODE_POWERDOWN = const(0x0000)
    CONFIG_MODE_SVOLT_TRIGGERED = const(0x0001)
    CONFIG_MODE_BVOLT_TRIGGERED = const(0x0002)
    CONFIG_MODE_SANDBVOLT_TRIGGERED = const(0x0003)
    CONFIG_MODE_ADCOFF = const(0x0004)
    CONFIG_MODE_SVOLT_CONTINUOUS = const(0x0005)
    CONFIG_MODE_BVOLT_CONTINUOUS = const(0x0006)
    CONFIG_MODE_SANDBVOLT_CONTINUOUS = const(0x0007)

    def __init__(self, i2c=I2C, addr: int = 0x40):
        self.i2c = i2c
        self.addr = addr

        self.buf = bytearray(2)
        
        # Due to fixed PCB design, hard coding in calibration value and config
        # VBUS_MAX = 16V
        # VSHUNT_MAX = 40mV
        # RSHUNT = 10mR
        # IMAX = VSHUNT_MAX / RSHUNT = 4A
        self._current_lsb = 0.001   # (IMAX / 4096) = 1mA per bit
        self._cal_value = 4096      # (0.04096 / (current_lsb * RSHUNT))
        self._power_lsb = 0.02      # 20 * current_lsb

        self.set_calibration(self._cal_value, 
            self.CONFIG_BVOLTAGERANGE_16V |
            self.CONFIG_GAIN_1_40MV |
            self.CONFIG_BADCRES_12BIT |
            self.CONFIG_SADCRES_12BIT_1S_532US |
            self.CONFIG_MODE_SANDBVOLT_CONTINUOUS)

    def _write_register(self, reg, value):
        self.buf[0] = (value >> 8) & 0xFF
        self.buf[1] = value & 0xFF
        self.i2c.writeto_mem(self.addr, reg, self.buf)

    def _read_register(self, reg):
        self.i2c.readfrom_mem_into(self.addr, reg & 0xff, self.buf)
        value = (self.buf[0] << 8) | (self.buf[1])
        return value
    
    def _to_signed(self, num):
        if num > 0x7FFF:
            num -= 0x10000
        return num

    def get_shunt_voltage(self):
        """The shunt voltage (between V+ and V-) in Volts (so +-.327V)"""
        value = self._to_signed(self._read_register(self.REG_SHUNT))
        # The least signficant bit is 10uV which is 0.00001 volts
        return value * 0.00001

    def get_bus_voltage(self):
        """The bus voltage (between V- and GND) in Volts"""
        raw_voltage = self._read_register(self.REG_BUS)

        # Shift to the right 3 to drop CNVR and OVF and multiply by LSB
        # Each least signficant bit is 4mV
        voltage_mv = self._to_signed(raw_voltage >> 3) * 4
        return voltage_mv * 0.001

    def get_current(self):
        """The current through the shunt resistor in milliamps."""
        # Write cal register as it is volatile and will break current and power readings if missing
        self._write_register(self.REG_CAL, self._cal_value)

        # Now we can safely read the CURRENT register!
        raw_current = self._to_signed(self._read_register(self.REG_CURRENT))
        return raw_current * self._current_lsb

    def set_calibration(self, cal_value, config):
        '''Set calibration value and config register values'''
        self._write_register(self.REG_CAL, cal_value)
        self._write_register(self.REG_CONFIG, config)