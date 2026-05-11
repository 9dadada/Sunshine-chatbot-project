"""
MQTT publish 테스트
HiveMQ 공개 브로커를 사용해서 메시지 한 번 보내기
"""
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# === 연결 정보 ===
BROKER_HOST = "broker.hivemq.com"  # 공개 브로커
BROKER_PORT = 1883
TOPIC = "sunshine/test/dahye-001"  # 다혜님 전용 토픽

# === MQTT 클라이언트 만들기 ===
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="rpi-test-dahye-001"
)

# === 브로커 연결 ===
print(f"브로커 연결 중: {BROKER_HOST}:{BROKER_PORT}")
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
print("연결 성공!")

# === 백그라운드 통신 시작 ===
client.loop_start()

# === 테스트 메시지 publish ===
payload = {
    "reading_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "device_id": "rpi-edge-node-01",
    "plant_id": "plant-001",
    "measured_at": datetime.now().astimezone().isoformat(),
    "temperature_c": 24.5,
    "humidity_pct": 55.2,
    "light_lux": 850.0,
    "soil_moisture_pct": 42.0,
}

print(f"\n토픽: {TOPIC}")
print(f"페이로드: {json.dumps(payload, indent=2, ensure_ascii=False)}")

result = client.publish(
    topic=TOPIC,
    payload=json.dumps(payload),
    qos=1,
)

# 발행 결과 확인 (2초 대기)
result.wait_for_publish(timeout=2)

if result.is_published():
    print("\n✅ 메시지 발행 성공!")
else:
    print("\n❌ 메시지 발행 실패")

# 정리
client.loop_stop()
client.disconnect()
print("MQTT 클라이언트 종료")