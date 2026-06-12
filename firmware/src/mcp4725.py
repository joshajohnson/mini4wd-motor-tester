# Thanks to Jean-Marie Prévost https://github.com/JeanMariePrevost/mcp4725-micropython

from machine import I2C


class MCP4725:
    """
    MicroPython Driver for the Microchip MCP4725 DAC.

    Example:

        i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))
        dac = MCP4725(i2c, vcc_mv=3.3)
        dac.set_value(2048) # By raw DAC value (0-4095)
        dac.set_voltage(1650)  # By millivoltage

    See datasheet: https://ww1.microchip.com/downloads/en/DeviceDoc/22039d.pdf

    """

    def __init__(self, i2c=I2C, addr: int = None, vcc_mv: float = 3300):
        self.i2c = i2c
        self.addr = addr
        self.vcc_mv = vcc_mv

    def set_value(self, value: int) -> None:
        """
        Set raw DAC output value (12 bit integer, 0-4095)
        Fast mode, does not write EEPROM.
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

    def set_voltage_mv(self, voltage_mv: int) -> None:
        """
        Set DAC output voltage.
        NOTE: Cannot truly set voltage, only used as a shorthand based on the reference voltage.
        """
        value = self._voltage_to_value(voltage_mv)
        self.set_value(value)

    def get_voltage_mv(self) -> int:
        """
        Get current DAC output voltage.
        NOTE: Cannot truly measure voltage, only used as a shorthand based on the reference voltage.
        """
        value = self.get_value()
        return self._value_to_voltage(value)

    def _value_to_voltage(self, value: int) -> int:
        """Internal: Convert raw DAC value to voltage"""
        return (value / 4095) * self.vcc_mv

    def _voltage_to_value(self, voltage_mv: int) -> int:
        """Internal: Convert voltage to raw DAC value"""
        return int((voltage_mv / self.vcc_mv) * 4095)
