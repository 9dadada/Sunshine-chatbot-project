"""
Sensor measurements
rule
- measurement interval : 5분
- measurement duration : 10초
-  : 2초
- 성공한 측정값들의 평균 반환
- 평균값 반환
- 평균값이 null이면 실패
"""
import time
from datetime import datetime

from sensors.dht22 import DHT22Sensor
from sensors.bh1750 import BH1750Sensor
from sensors.soil_humid import SoilHumiditySensor
import config

class Measurement:
    def __init__(self):
        self.dht22 = DHT22Sensor()
        self.bh1750 = BH1750Sensor()
        self.soil_sensor = SoilHumiditySensor()

    def perform_measurement(self):
        # 루프용 time
        start_time = time.time()
        end_time = start_time + config.MEASUREMENT_DURATION

        # 전송용 time : ISO 8601 형식
        measured_at = datetime.now().astimezone().isoformat()

        # 측정값 저장용 리스트
        temp = []
        humid = []
        light = []
        soil_humid = []

        while time.time() < end_time:
            # 센서 함수 호출
            dht22_temp, dht22_humid = self.dht22.read()
            bh1750_light = self.bh1750.read()
            soil_humid_value = self.soil_sensor.read()

            # 측정값이 None이 아니면 리스트에 추가
            if dht22_temp is not None:
                temp.append(dht22_temp)
            if dht22_humid is not None:
                humid.append(dht22_humid)
            if bh1750_light is not None:
                light.append(bh1750_light)
            if soil_humid_value is not None:
                soil_humid.append(soil_humid_value)
            
            # 센서 측정 간격
            time.sleep(config.MEASUREMENT_INTERVAL_SECONDS)

        #평균값
        send_temp = round(sum(temp) / len(temp), 1) if temp else None
        send_humid = round(sum(humid) / len(humid), 1) if humid else None
        send_light = round(sum(light) / len(light), 1) if light else None
        send_soil_humid = round(sum(soil_humid) / len(soil_humid), 1) if soil_humid else None

        return {
                "measured_at": measured_at,
                "temperature_c": send_temp,
                "humidity_pct": send_humid,
                "light_lux": send_light,
                "soil_moisture_pct": send_soil_humid
                }

    # 모듈 단독 실행 테스트
if __name__ == "__main__":
    import json
    
    print("Measurement 테스트")
    print("=" * 50)
    
    service = Measurement()
    result = service.perform_measurement()
    
    print("\n[결과]")
    print(json.dumps(result, indent=2, ensure_ascii=False))
