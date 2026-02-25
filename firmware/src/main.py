import machine
import tmp1075
import time

i2c = machine.I2C(scl=machine.Pin(9), sda=machine.Pin(8))

print('Scan i2c bus...')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))

  for device in devices:  
    print("Address: ",hex(device))

temp_sensor = tmp1075.TMP1075(i2c)

print(hex(temp_sensor.get_die_id()))

while True:
    temp_c = temp_sensor.get_temperature()
    print("Temperature: {:.2f} °C".format(temp_c))
    time.sleep(1)