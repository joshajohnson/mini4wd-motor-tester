# Thanks to Jean-Marie Prévost https://github.com/JeanMariePrevost/mcp4725-micropython

from machine import I2C

class MCP4725:

    '''
    MicroPython Driver for the Microchip MCP4725 DAC.

    Example:

        i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))
        dac = MCP4725(i2c, vcc=3.3)
        dac.set_value(2048) # By raw DAC value (0-4095)
        dac.set_voltage(1.65)  # By voltage

    See datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf
    
    '''

    def __init__(self, i2c=I2C, addr: int = 0x60, vcc: float = 3.3):
        self.i2c = i2c
        self.addr = addr
        self.vcc = vcc

    def set_value(self, value: int) -> None:
        """
        Set raw DAC output value (12 bit integer, 0-4095)
        Fast mode, does not write EEPROM.
        :param value: 12-bit integer (0-4095)
        """
        value = max(0, min(4095, int(value)))
        buf = bytearray(3)
        buf[0] = 0x40  # Fast mode command
        buf[1] = value >> 4
        buf[2] = (value & 0xF) << 4
        self.i2c.writeto(self.addr, buf)

    def get_value(self) -> int:
        """Get current raw DAC value (12 bit integer, 0-4095)"""
        buf = self.i2c.readfrom(self.addr, 5)
        return ((buf[1] << 4) | (buf[2] >> 4)) & 0xFFF

    def set_voltage(self, voltage: float) -> None:
        """
        Set DAC output voltage.
        NOTE: Cannot truly measure voltage, only used as a shorthand based on the reference voltage.
        :param voltage: Desired output voltage (0 to VCC)
        """
        value = self._voltage_to_value(voltage)
        self.set_value(value)

    def get_voltage(self) -> float:
        """
        Get current DAC output voltage.
        NOTE: Cannot truly measure voltage, only used as a shorthand based on the reference voltage.
        :return: Current voltage as float
        """
        value = self.get_value()
        return self._value_to_voltage(value)
    
    def _value_to_voltage(self, value: int) -> float:
        """Internal: Convert raw DAC value to voltage"""
        return (value / 4095) * self.vcc

    def _voltage_to_value(self, voltage: float) -> int:
        """Internal: Convert voltage to raw DAC value"""
        return int((voltage / self.vcc) * 4095)
