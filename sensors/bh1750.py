"""
BH1750 조도 센서 모듈
I2C 통신, 주소 0x23
"""
import board
import busio
import adafruit_bh1750


class BH1750Sensor:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.bh1750 = adafruit_bh1750.BH1750(i2c)

    def read(self):
        """
        조도값 반환 (단위: lux)
        실패 시 None
        """
        try:
            return self.bh1750.lux
        except Exception as e:
            print(f"[BH1750] 예외 발생: {e}")
            return None


# 모듈 단독 실행 테스트
if __name__ == "__main__":
    import time
    
    print("BH1750 모듈 테스트 (Ctrl+C로 종료)")
    sensor = BH1750Sensor()
    
    try:
        while True:
            light = sensor.read()
            if light is not None:
                print(f"조도: {light:.1f} lux")
            else:
                print("측정 실패")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n종료")