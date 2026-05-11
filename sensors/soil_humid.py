"""
soil moisture sensor module
"""

import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

import config

class SoilHumiditySensor:
    def __init__(self, channel=MCP.P0):
        # air and water value
        self.AIR_VALUE = config.SOIL_AIR_VALUE
        self.WATER_VALUE = config.SOIL_WATER_VALUE
        
        # SPI bus
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.cs = digitalio.DigitalInOut(board.CE0) 
        self.mcp3008 = MCP.MCP3008(self.spi, self.cs)
        
        # input channel (CH0)
        self.soil_channel = AnalogIn(self.mcp3008, MCP.P0)

    def read(self):
        """percent"""
        raw_value = self.soil_channel.value
        percent = (self.AIR_VALUE - raw_value) / (self.AIR_VALUE - self.WATER_VALUE) * 100
        percent = max(0, min(100, percent))  # 0~100
        return percent

    def cleanup(self):
        """SPI bus cleanup"""
        try:
            self.spi.deinit()
        except Exception:
            pass

# test code
if __name__ == "__main__":
    import time
    
    print("soill moisture sensor test")
    sensor = SoilHumiditySensor()
    
    try:
        while True:
            humidity = sensor.read()
            if humidity is not None:
                print(f"soil moisture: {humidity:.1f} %")
            else:
                print("measurement fail")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\ninterrupt")
