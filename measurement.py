"""
Sensor measurements
rule
- sending interval : 5 min
- measurement duration : 10 sec
- measurement interval : 2 sec
- Return mean value
- if mean value = null -> failure
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
        # time for roop
        start_time = time.time()
        end_time = start_time + config.MEASUREMENT_DURATION

        # time for transmit: ISO 8601
        measured_at = datetime.now().astimezone().isoformat()

        # storage list
        temp = []
        humid = []
        light = []
        soil_humid = []

        while time.time() < end_time:
            # call sensor func
            dht22_temp, dht22_humid = self.dht22.read()
            bh1750_light = self.bh1750.read()
            soil_humid_value = self.soil_sensor.read()

            # if value is not None add in list
            if dht22_temp is not None:
                temp.append(dht22_temp)
            if dht22_humid is not None:
                humid.append(dht22_humid)
            if bh1750_light is not None:
                light.append(bh1750_light)
            if soil_humid_value is not None:
                soil_humid.append(soil_humid_value)
            
            # measurement interval
            time.sleep(config.MEASUREMENT_INTERVAL_SECONDS)

        # calculate mean value
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

    # test code
if __name__ == "__main__":
    import json
    
    print("Measurement test")
    print("=" * 50)
    
    service = Measurement()
    result = service.perform_measurement()
    
    print("\n[result]")
    print(json.dumps(result, indent=2, ensure_ascii=False))
