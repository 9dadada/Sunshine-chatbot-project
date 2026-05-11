"""
통신 메인 모듈
통신 주기 : 5분
MQTT 프로토콜 사용
"""

import time
import schedule

from measurement import Measurement
from mqtt_client import MQTTPublisher
import config


def main():
    print("=" * 60)
    print("Sunshine sensor system start")
    print(f"   Device ID: {config.DEVICE_ID}")
    print(f"   Plant ID: {config.PLANT_ID}")
    print(f"   측정 주기: {config.SENDING_INTERVAL_MINUTES}분마다")
    print("=" * 60)
    
    # 객체 생성
    measurement_service = Measurement()
    publisher = MQTTPublisher()
    
    # MQTT 연결 (한 번만)
    publisher.connect()
    
    def measure_and_publish():
        print(f"\n[{time.strftime('%H:%M:%S')}] Measurement start")
        data = measurement_service.perform_measurement()
        publisher.publish_measurement(data)
    
    # 시작하자마자 한 번 측정
    measure_and_publish()
    
    # 5분마다 반복 스케줄
    schedule.every(config.SENDING_INTERVAL_MINUTES).minutes.do(measure_and_publish)
    
    # 메인 루프
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[Exit request detected]")
    finally:
        # Cleanup
        print("[Cleanup] Cleaning up resources...")
        measurement_service.dht22.cleanup()
        publisher.disconnect()
        print("[Cleanup] Done")


if __name__ == "__main__":
    main()