import time
import board
import adafruit_bh1750

i2c = board.I2C()
bh1750 = adafruit_bh1750.BH1750(i2c)

while True:
    light = bh1750.lux
    print(f"조도: {bh1750.lux:.1f} lux")
    time.sleep(2)
