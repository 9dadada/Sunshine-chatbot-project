"""
Main module of communication
communication interval : 5 min
MQTT protocols
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
    print(f"   sending interval: {config.SENDING_INTERVAL_MINUTES}min")
    print("=" * 60)
    
    # Creat object
    measurement_service = Measurement()
    publisher = MQTTPublisher()
    
    # MQTT connection
    publisher.connect()
    
    def measure_and_publish():
        print(f"\n[{time.strftime('%H:%M:%S')}] Measurement start")
        data = measurement_service.perform_measurement()
        publisher.publish_measurement(data)
    
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
        print("\n\n[Exit request detected]")
    finally:
        # Cleanup
        print("[Cleanup] Cleaning up resources...")
        measurement_service.dht22.cleanup()
        publisher.disconnect()
        print("[Cleanup] Done")


if __name__ == "__main__":
    main()
