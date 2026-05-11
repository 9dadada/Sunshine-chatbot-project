"""
프로젝트 전역 설정값
"""

# 디바이스 식별 
DEVICE_ID = "rpi-edge-node-01"
PLANT_ID = "plant-001"  # 임시값. 나중에 UUID로 변경

# MQTT 브로커 
MQTT_BROKER = "broker.hivemq.com"  #"mock"  # 임시
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_QOS = 1

#  토픽 
# 토픽은 device_id에 맞춰 자동 생성
MQTT_TOPIC = f"sensor/readings/{DEVICE_ID}"

# 측정 설정 
MEASUREMENT_DURATION = 10  # 한 주기당 측정 지속 시간 (초)
MEASUREMENT_INTERVAL_SECONDS = 2  # 센서 측정 간격

# 전송 주기
SENDING_INTERVAL_MINUTES = 0.5

# 토양 센서 보정값
# 직접 측정한 값 (raw)
SOIL_AIR_VALUE = 54260   # 공기 중 = 0%
SOIL_WATER_VALUE = 24920  # 물 속 = 100%