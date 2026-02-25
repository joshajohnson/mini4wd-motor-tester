import machine
import time

# I2C Drivers
import tmp1075

# Init I2C
i2c = machine.I2C(sda=machine.Pin(8), scl=machine.Pin(9))

def i2cdetect(i2c):
  print("     " + " ".join(f"{x:02x}" for x in range(16)))
  devices = set(i2c.scan())
  for row in range(8):
    line = f"{row << 4:02x}:"
    for col in range(16):
      addr = (row << 4) | col
      if addr < 0x03 or addr > 0x77:
        line += "   "
      elif addr in devices:
        line += f" {addr:02x}"
      else:
        line += " --"
    print(line)

i2cdetect(i2c)

temp_sensor = tmp1075.TMP1075(i2c)

while True:
  temp = temp_sensor.get_temperature()
  print("Temperature: {:.2f} °C".format(temp))
  time.sleep(1)