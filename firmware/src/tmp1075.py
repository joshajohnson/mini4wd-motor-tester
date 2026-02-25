from machine import I2C

class TMP1075:
    I2C_ADDR = 0x48
    REG_TEMP = 0x00
    REG_CONFIG = 0x01
    REG_DIEID = 0x0F

    def __init__(self, i2c: I2C, addr: int = I2C_ADDR):
        self.i2c = i2c
        self.addr = addr

    def get_temp_raw(self):
        data = self.i2c.readfrom_mem(self.addr, self.REG_TEMP, 2)
        raw = (data[0] << 8) | data[1]
        # 12-bit resolution, left-justified in 16 bits
        raw = raw >> 4
        # Handle negative temperatures (two's complement)
        if raw & 0x800:
            raw -= 1 << 12
        return raw

    def get_temperature(self):
        raw = self.get_temp_raw()
        temp_c = raw * 0.0625
        return temp_c

    def set_config(self, config):
        buf = bytearray([(config >> 8) & 0xFF, config & 0xFF])
        self.i2c.writeto_mem(self.addr, self.REG_CONFIG, buf)

    def get_config(self):
        data = self.i2c.readfrom_mem(self.addr, self.REG_CONFIG, 2)
        return (data[0] << 8) | data[1]
    
    def get_die_id(self):
        data = self.i2c.readfrom_mem(self.addr, self.REG_DIEID, 2)
        return (data[0] << 8) | data[1]
