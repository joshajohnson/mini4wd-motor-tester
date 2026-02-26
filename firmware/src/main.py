import machine
import time

import psu

# Init I2C
i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))

psu = psu.PSU(i2c)
psu.set_voltage(2)
psu.enable()


while True:
    print(f"Voltage: {psu.get_voltage():.2f} V, Current: {psu.get_current():.2f} mA")
    time.sleep_ms(100)



# def i2cdetect(i2c):
#   print("     " + " ".join(f"{x:02x}" for x in range(16)))
#   devices = set(i2c.scan())
#   for row in range(8):
#     line = f"{row << 4:02x}:"
#     for col in range(16):
#       addr = (row << 4) | col
#       if addr < 0x03 or addr > 0x77:
#         line += "   "
#       elif addr in devices:
#         line += f" {addr:02x}"
#       else:
#         line += " --"
#     print(line)

# i2cdetect(i2c)