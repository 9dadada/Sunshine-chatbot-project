"""
토양 습도 센서 모듈
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
        # 보정값
        self.AIR_VALUE = config.SOIL_AIR_VALUE
        self.WATER_VALUE = config.SOIL_WATER_VALUE
        
        # SPI bus
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.cs = digitalio.DigitalInOut(board.CE0) 
        self.mcp3008 = MCP.MCP3008(self.spi, self.cs)
        
        # 토양 센서 입력 채널 (CH0)
        self.soil_channel = AnalogIn(self.mcp3008, MCP.P0)

    def read(self):
        """백분율로 변환 후 반환"""
        raw_value = self.soil_channel.value
        percent = (self.AIR_VALUE - raw_value) / (self.AIR_VALUE - self.WATER_VALUE) * 100
        percent = max(0, min(100, percent))  # 0~100 범위로 제한
        return percent

    def cleanup(self):
        """SPI 버스 정리"""
        try:
            self.spi.deinit()
        except Exception:
            pass

# 모듈 단독 실행 테스트
if __name__ == "__main__":
    import time
    
    print("토양 습도 센서 모듈 테스트 (Ctrl+C로 종료)")
    sensor = SoilHumiditySensor()
    
    try:
        while True:
            humidity = sensor.read()
            if humidity is not None:
                print(f"토양 습도: {humidity:.1f} %")
            else:
                print("측정 실패")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n종료")