"""
MQTT publish module
- connection with broker
- creat payload and publish
- reading_id automatic generation
- in case of connection failure, retrying automatically
"""
import json
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
import config

logger = logging.getLogger(__name__)

class MQTTPublisher:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.DEVICE_ID
        )
        # retrying automatically when connection failure
        self.client.on_disconnect = self._on_disconnect

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        if reason_code != 0:  # 0 = clean disconnect, 1 = unexpected disconnect
            logger.warning(f"MQTT unexpected disconnection. Reconnecting...")
            self._reconnect()

    def _reconnect(self, max_retries=config.MAX_RETRIES):
        for attempt in range(1, max_retries + 1):
            try: 
                logger.info(f"Reconnect attempt {attempt}/{max_retries}")
                self.client.connect()
                logger.info("Reconnected successfully")
                return True
            except Exception as e:
                logger.error(f"Reconnect attempt {attempt} failed: {e}")
                time.sleep(5)
        logger.error("All reconnect attempts failed")
        return False

    def connect(self, max_retries=config.MAX_RETRIES):
        """connection with broker"""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Broker connecting: {config.MQTT_BROKER}:{config.MQTT_PORT} (attempt {attempt}/{max_retries})")
                self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_KEEPALIVE)
                self.client.loop_start()
                logger.info("MQTT Connected")
                return True
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {e}")
                time.sleep(5)
        logger.error("All connection attempts failed")
        return False

    def disconnect(self):
        """disconnection"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT Disconnected")

    def _generate_reading_id(self):
        """Generate reading_id: rdg-{device_id}-{YYYYMMDDTHHMMSS}"""
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return f"rdg-{config.DEVICE_ID}-{timestamp}"

    def publish_measurement(self, measurement_data):
        # payload
        payload = {
            "reading_id": self._generate_reading_id(),
            "device_id": config.DEVICE_ID,
            "plant_id": config.PLANT_ID,
            **measurement_data,  # measured_at + 4 measurement values
        }

        try:
            logger.info(f"MQTT Topic: {config.MQTT_TOPIC}")

            # DEBUGING payload
            logger.debug(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            result = self.client.publish(
                topic=config.MQTT_TOPIC,
                payload=json.dumps(payload),
                qos=config.MQTT_QOS,
            )
            result.wait_for_publish(timeout=5)
            if result.is_published():
                logger.info("Publish Success")
                return True
            else:
                logger.error("Publish Failed")
                return False
     
        except Exception as e:
            # try in next duration
            logger.error(f"Publish error: {e}")
            return False

        