# esp32-soil-01
# main code

import time
import machine
from machine import Pin, ADC, deepsleep, wake_reason, EXT0_WAKE
import network
import ujson
import ubinascii
from umqtt.simple import MQTTClient
import esp32

# ── config ────────────────────────────────────────────────────────────────────
DEVICE_ID      = "esp32-soil-01"
PLANT_ID       = "plant-001"  # 백엔드 배포 후 변경
MQTT_BROKER    = "broker.hivemq.com"  # 백엔드 배포 후 변경
MQTT_PORT      = 1883
MQTT_TOPIC     = f"sensor/readings/{DEVICE_ID}"
SLEEP_MS       = 5 * 60 * 1000  # 5분

SOIL_PIN       = 34
AIR_VAL        = 3400
WATER_VAL      = 1465

BUTTON_PIN     = 32

# ── button ────────────────────────────────────────────────────────────────────
def check_button():
    button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    if button.value() == 0:
        return True
    return False

# ── deepsleep ─────────────────────────────────────────────────────────────────
def go_deepsleep():
    print("→ deepsleep")
    esp32.wake_on_ext0(pin=Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP), level=0)
    deepsleep(SLEEP_MS)

# ── sensor ────────────────────────────────────────────────────────────────────
def read_soil():
    adc = ADC(Pin(SOIL_PIN))
    adc.atten(ADC.ATTN_11DB)

    # 10회 측정 후 평균
    readings = []
    for _ in range(10):
        readings.append(adc.read())
        time.sleep(0.1)
    raw = sum(readings) // len(readings)

    # 0~100% 변환
    pct = (AIR_VAL - raw) / (AIR_VAL - WATER_VAL) * 100
    pct = max(0.0, min(100.0, pct))

    print(f"Soil raw: {raw}, moisture: {pct:.1f}%")
    return round(pct, 1)

# ── Wi-Fi ─────────────────────────────────────────────────────────────────────
def get_wlan():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected() and wlan.ifconfig()[0] != '0.0.0.0':
        return wlan
    return None

# ── MQTT ─────────────────────────────────────────────────────────────────────
def get_timestamp():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+09:00".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def get_reading_id():
    t = time.localtime()
    return "rdg-{}-{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}".format(
        DEVICE_ID, t[0], t[1], t[2], t[3], t[4], t[5]
    )

def publish(soil_moisture_pct):
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, MQTT_BROKER, port=MQTT_PORT)

    try:
        client.connect()
        payload = ujson.dumps({
            "reading_id": get_reading_id(),
            "device_id": DEVICE_ID,
            "plant_id": PLANT_ID,
            "measured_at": get_timestamp(),
            "soil_moisture_pct": soil_moisture_pct
        })
        client.publish(MQTT_TOPIC, payload)
        print(f"MQTT published: {payload}")
        client.disconnect()
        return True
    except Exception as e:
        print(f"MQTT error: {e}")
        return False

# ── run ───────────────────────────────────────────────────────────────────────

# Wi-Fi 연결 확인
wlan = get_wlan()
if not wlan:
    print("Wi-Fi not connected → deepsleep")
    go_deepsleep()

# 버튼 체크 (즉시 딥슬립)
if check_button():
    print("Button pressed → deepsleep")
    go_deepsleep()

# 센서 측정
soil_moisture_pct = read_soil()

# MQTT 전송
publish(soil_moisture_pct)

# 버튼 체크 (전송 후 딥슬립 전)
if check_button():
    print("Button pressed → deepsleep")
    go_deepsleep()

# 5분 딥슬립
print(f"Sleep {SLEEP_MS // 1000}s")
go_deepsleep()