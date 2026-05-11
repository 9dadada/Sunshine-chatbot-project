"""
MQTT 발행 모듈
- 브로커 연결
- 측정 데이터를 페이로드로 만들어 publish
- reading_id 자동 생성
"""
import json
from datetime import datetime

import paho.mqtt.client as mqtt
import config


class MQTTPublisher:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.DEVICE_ID
        )

    def connect(self):
        """브로커 연결"""
        print(f"[MQTT] Broker connecting: {config.MQTT_BROKER}:{config.MQTT_PORT}")
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
        self.client.loop_start()
        print("[MQTT] Connected")

    def disconnect(self):
        """브로커 연결 해제"""
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected")

    def _generate_reading_id(self):
        """reading_id 생성: rdg-{device_id}-{YYYYMMDDTHHMMSS}"""
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return f"rdg-{config.DEVICE_ID}-{timestamp}"

    def publish_measurement(self, measurement_data):
        """
        측정 데이터를 받아 페이로드 조립 후 publish
        
        measurement_data: measurement.py의 perform_measurement() 결과
            {
                "measured_at": "...",
                "temperature_c": ...,
                "humidity_pct": ...,
                "light_lux": ...,
                "soil_moisture_pct": ...
            }
        """
        # payload
        payload = {
            "reading_id": self._generate_reading_id(),
            "device_id": config.DEVICE_ID,
            "plant_id": config.PLANT_ID,
            **measurement_data,  # measured_at + 4개 측정값
        }

        print(f"[MQTT] Topic: {config.MQTT_TOPIC}")
        print(f"[MQTT] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # publish
        result = self.client.publish(
            topic=config.MQTT_TOPIC,
            payload=json.dumps(payload),
            qos=config.MQTT_QOS,
        )
        result.wait_for_publish(timeout=5)

        if result.is_published():
            print("[MQTT] Success")
            return True
        else:
            print("[MQTT] Failed")
            return False


# 모듈 단독 실행 테스트
if __name__ == "__main__":
    print("MQTTPublisher Test")
    print("=" * 50)
    
    # 가짜 측정 데이터로 테스트
    fake_data = {
        "measured_at": datetime.now().astimezone().isoformat(),
        "temperature_c": 24.5,
        "humidity_pct": 55.2,
        "light_lux": 850.0,
        "soil_moisture_pct": 42.0,
    }
    
    publisher = MQTTPublisher()
    
    try:
        publisher.connect()
        publisher.publish_measurement(fake_data)
    finally:
        publisher.disconnect()