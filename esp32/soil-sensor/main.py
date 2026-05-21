# esp32-soil-01
# main code

import time
import machine
from machine import Pin, ADC, deepsleep
import network
import ujson
import ubinascii
import ntptime
from umqtt.simple import MQTTClient
import esp32

from logger import append_data

# config
DEVICE_ID      = "esp32-soil-01"
PLANT_ID       = "plant-001" 
MQTT_BROKER    = "3.26.39.221"
MQTT_PORT      = 1883
MQTT_TOPIC     = f"sensor/readings/{DEVICE_ID}"
SLEEP_MS       = 5 * 60 * 1000  # 5min

SOIL_PIN       = 34
AIR_VAL        = 3400
WATER_VAL      = 1465

BUTTON_PIN     = 32

# NTP
def sync_time():
    try:
        ntptime.settime()
    except Exception as e:
        print(f"NTP sync failed: {e}")

# deepsleep
def go_deepsleep():
    print("→ deepsleep")
    esp32.wake_on_ext0(pin=Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP), level=0)
    deepsleep(SLEEP_MS)

# sensor
def read_soil():
    adc = ADC(Pin(SOIL_PIN))
    adc.atten(ADC.ATTN_11DB)

    # average of 10 readings
    readings = []
    for _ in range(10):
        readings.append(adc.read())
        time.sleep(1)
    raw = sum(readings) // len(readings)

    # 0~100%
    pct = (AIR_VAL - raw) / (AIR_VAL - WATER_VAL) * 100
    pct = max(0.0, min(100.0, pct))

    print(f"Soil raw: {raw}, moisture: {pct:.1f}%")
    return round(pct, 1)

# Wi-Fi
def get_wlan():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected() and wlan.ifconfig()[0] != '0.0.0.0':
        return wlan
    return None

# MQTT
def get_timestamp():
    t = time.localtime(time.time() + 9 * 3600)  # KST
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+09:00".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def get_reading_id():
    t = time.localtime(time.time() + 9 * 3600) # KST
    return "rdg-{}-{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}".format(
        DEVICE_ID, t[0], t[1], t[2], t[3], t[4], t[5]
    )

def make_payload(soil_moisture_pct):
    return ujson.dumps({
        "reading_id": get_reading_id(),
        "device_id": DEVICE_ID,
        "plant_id": PLANT_ID,
        "measured_at": get_timestamp(),
        "soil_moisture_pct": soil_moisture_pct
    })

def publish(payload):
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, MQTT_BROKER, port=MQTT_PORT)

    try:
        client.connect()
        client.publish(MQTT_TOPIC, payload)
        print(f"MQTT published: {payload}")
        client.disconnect()
        return True
    except Exception as e:
        print(f"MQTT error: {e}")
        return False

# run

# Wi-Fi connection check
wlan = get_wlan()
if not wlan:
    print("Wi-Fi not connected → deepsleep")
    go_deepsleep()

# NTP synchronise
sync_time()

# sensor measurement
soil_moisture_pct = read_soil()

# build payload + local backup (always saved)
payload = make_payload(soil_moisture_pct)
append_data(payload)

# MQTT publish (retry once on failure)
if not publish(payload):
    time.sleep(2)
    publish(payload)

# Button check
check_button()

# 5min deep-sleep
print(f"Sleep {SLEEP_MS // 1000}s")
go_deepsleep()