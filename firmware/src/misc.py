# Miscallaneous utilities which don't have a better place to live

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