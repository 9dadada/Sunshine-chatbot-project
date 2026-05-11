"""
MQTT publish module
- connection with broker
- creat payload and publish
- reading_id automatic generation
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
        """connection with broker"""
        print(f"[MQTT] Broker connecting: {config.MQTT_BROKER}:{config.MQTT_PORT}")
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
        self.client.loop_start()
        print("[MQTT] Connected")

    def disconnect(self):
        """disconnection"""
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected")

    def _generate_reading_id(self):
        """Generate reading_id: rdg-{device_id}-{YYYYMMDDTHHMMSS}"""
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return f"rdg-{config.DEVICE_ID}-{timestamp}"

    def publish_measurement(self, measurement_data):
        """
        create paylaod and publish
        
        measurement_data: measurement.py의 perform_measurement() result
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
            **measurement_data,  # measured_at + 4 measurement values
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


# test code
if __name__ == "__main__":
    print("MQTTPublisher Test")
    print("=" * 50)
    
    # fake data test
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
