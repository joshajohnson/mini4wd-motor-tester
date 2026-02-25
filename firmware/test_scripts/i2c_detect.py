import machine
i2c = machine.I2C(scl=machine.Pin(9), sda=machine.Pin(8))

print('Scan i2c bus...')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))

  for device in devices:  
    print("Address: ",hex(device))