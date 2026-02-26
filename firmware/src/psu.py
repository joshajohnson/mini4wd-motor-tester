from machine import I2C, Pin

import mcp4725
import ina219

class PSU:

    '''
    Control logic for the adjustable buck converter used to power the motor.
    Uses the MCP4725 DAC to set the output voltage.

    Example:

        psu = PSU(i2c, dac_addr=0x60, imon_addr=0x40)
        psu.enable()
        psu.disable()
        psu.set_voltage(1.65)  # Set regulator output voltage to 1.65V
        psu.get_voltage()  # Use current sensor to measure output voltage
        psu.get_current()  # Use current sensor to measure output current
    
    '''

    def __init__(self, i2c=I2C, en_pin: int = 16, dac_addr: int = 0x60, imon_addr: int = 0x40):
        if not i2c:
            raise ValueError('I2C object needed')
        self.i2c = i2c
        self.dac_addr = dac_addr
        self.imon_addr = imon_addr
        self.dac = mcp4725.MCP4725(i2c, addr=self.dac_addr)
        self.imon = ina219.INA219(i2c, addr=self.imon_addr)

        self.reg_enable_pin = Pin(en_pin, Pin.OUT, Pin.PULL_DOWN)

    def enable(self):
        '''Enable buck reg with enable pin'''
        self.reg_enable_pin.value(1)

    def disable(self):
        '''Disable buck reg with enable pin'''
        self.reg_enable_pin.value(0)
        
    def set_voltage(self, voltage: float):
        '''Given desired output voltage, calculate DAC voltage and set accordingly'''

        # Output voltage configured per ADI / Maxim appnote
        # A 3-Step Approach for Designing a Variable Output Buck Regulator

        # R1 = 100K, R2 = 33K, R3 = 100K
        # VREF_FB = 0.8V, DAC Swing = 0-3.3V
        # Constants were determined emperically on one unit, don't ask me about per unit calibration

        dac_voltage = (4.06 - voltage) / 1.01
        self.dac.set_voltage(dac_voltage)

    def get_voltage(self):
        '''Measure output voltage using current sensor'''
        return self.imon.get_bus_voltage()
    
    def get_current(self):
        '''Measure output current using current sensor'''
        return self.imon.get_current()

