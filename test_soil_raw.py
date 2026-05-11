import time
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# 측정시간
time_sleep = 15 # sec

# 보정값
AIR_VALUE = 54260    # 공기 중 (마름) - 0%
WATER_VALUE = 24920  # 물속 (젖음) - 100%

# Creat SPI bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# CS는 CE0 (chip select)
cs = digitalio.DigitalInOut(board.CE0)

# Create mcp3008
mcp3008 = MCP.MCP3008(spi, cs)

# 토양 센서 input = MCP3008의 CH0
# 아날로그 입력
soil_channel = AnalogIn(mcp3008, MCP.P0)

def raw_to_percent(raw):
    """원시값을 0~100% 백분율로 변환"""
    percent = (AIR_VALUE - raw) / (AIR_VALUE - WATER_VALUE) * 100
    # 0~100 범위로 제한
    percent = max(0, min(100, percent))
    return percent


print("토양 센서 원시값(raw) 측정 시작 (Ctrl+C로 종료)")
print("-" * 40)

try:
    while True:
        raw_value = soil_channel.value  # 0 ~ 65535 (16bit로 변환된 값)
        soil_moisture = raw_to_percent(raw_value)
        print(f"raw: {raw_value:>6}  |  수분: {soil_moisture:5.1f} %")
        time.sleep(time_sleep)
except KeyboardInterrupt:
    print("\n종료")