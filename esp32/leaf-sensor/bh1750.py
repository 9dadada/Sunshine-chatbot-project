# BH1750 ambient light sensor driver (MicroPython)

import time

# measurement modes
CONT_HIRES_1 = 0x10  # continuous, 1 lx resolution, 120ms typ
ONE_HIRES_1  = 0x20  # one-time,   1 lx resolution, 120ms typ
POWER_ON     = 0x01
RESET        = 0x07

MEASURE_DELAY_MS = 180  # max 180ms for high-res mode

class BH1750:
    def __init__(self, i2c, addr=0x23):
        self.i2c = i2c
        self.addr = addr

    def _cmd(self, c):
        self.i2c.writeto(self.addr, bytes([c]))

    def read_lux(self):
        # one-time high-res measurement (auto power-down after)
        self._cmd(ONE_HIRES_1)
        time.sleep_ms(MEASURE_DELAY_MS)
        data = self.i2c.readfrom(self.addr, 2)
        raw = (data[0] << 8) | data[1]
        return raw / 1.2
