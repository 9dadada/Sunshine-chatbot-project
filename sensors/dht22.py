"""
DHT22 온습도 센서 모듈
GPIO 4 (Pin 7) 사용
"""
import board
import adafruit_dht


class DHT22Sensor:
    def __init__(self, pin=board.D4):
        self.dht = adafruit_dht.DHT22(pin)

    def read(self):
        """
        측정값 반환: (temperature, humidity)
        실패 시 (None, None)
        """
        try:
            return self.dht.temperature, self.dht.humidity
        except RuntimeError:
            return None, None
        except Exception as e:
            print(f"[DHT22] 예외 발생: {e}")
            return None, None

    def cleanup(self):
        try:
            self.dht.exit()
        except Exception:
            pass


# 모듈 단독 실행 테스트
if __name__ == "__main__":
    import time
    
    print("DHT22 모듈 테스트 (Ctrl+C로 종료)")
    sensor = DHT22Sensor()
    
    try:
        while True:
            temp, hum = sensor.read()
            if temp is not None:
                print(f"온도: {temp:.1f}°C  |  습도: {hum:.1f}%")
            else:
                print("측정 실패 (재시도 중...)")
            time.sleep(2)
    except KeyboardInterrupt:
        sensor.cleanup()
        print("\n종료")