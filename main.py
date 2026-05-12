"""
Main module of communication
communication interval : 5 min
MQTT protocols
"""

import time
import logging
import logging.handlers
import schedule
from measurement import Measurement
from mqtt_client import MQTTPublisher
import config

# Logging setup
logging.basicConfig(
	level = config.LOG_LEVEL,
	format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes = 10*1024*1024,  # 10MB
            backupCount = 3
            ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("Sunshine sensor system start")
    logger.info(f"   Device ID: {config.DEVICE_ID}")
    logger.info(f"   Plant ID: {config.PLANT_ID}")
    logger.info(f"   sending interval: {config.SENDING_INTERVAL_MINUTES}min")
    logger.info("=" * 60)
    
    # Creat object
    measurement_service = Measurement()
    publisher = MQTTPublisher()
    
    # MQTT connection + error handling
    if not publisher.connect():
        logger.error("Failed to connect to MQTT broker. Exiting.")
        return
    
    def measure_and_publish():
        logger.info("Measurement start")
        data = measurement_service.perform_measurement()
        result = publisher.publish_measurement(data)
        if not result:
            logger.error("Publish failed. Will retry next cycle.")
    
    # measurement
    measure_and_publish()
    
    # scheduling (per 5 minutes)
    schedule.every(config.SENDING_INTERVAL_MINUTES).minutes.do(measure_and_publish)
    
    # main roop
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exit request detected")
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        measurement_service.dht22.cleanup()
        publisher.disconnect()
        logger.info("Cleanup done")


if __name__ == "__main__":
    main()
