"""
Project Global Settings
"""

# Device Identification
DEVICE_ID = "rpi-edge-node-01"
PLANT_ID = "plant-001"  # temporary value

# MQTT broker
MQTT_BROKER = "broker.hivemq.com"  #"mock"  # temporary
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

# Topic
# automatic generation
MQTT_TOPIC = f"sensor/readings/{DEVICE_ID}"

# measurement settings 
MEASUREMENT_DURATION = 10  # measurenet duration per cycle
MEASUREMENT_INTERVAL_SECONDS = 2  # measurent interval (seconds)

# sending setting
SENDING_INTERVAL_MINUTES = 0.5

# soil moisture correction
# self-measurement in air and water condition
SOIL_AIR_VALUE = 54260   # in the air = 0%
SOIL_WATER_VALUE = 24920  # in the water = 100%
