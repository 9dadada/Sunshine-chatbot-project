# esp32-leaf-01
# main code

import time
import dht
import machine
from machine import Pin, I2C, deepsleep
import network
import ujson
import ubinascii
import ntptime
from umqtt.simple import MQTTClient
import esp32

from bh1750 import BH1750
from logger import append_data

# config
DEVICE_ID      = "esp32-leaf-01"
PLANT_ID       = "plant-001"
MQTT_BROKER    = "3.26.39.221"
MQTT_PORT      = 1883
MQTT_TOPIC     = f"sensor/readings/{DEVICE_ID}"
SLEEP_MS       = 5 * 60 * 1000  # 5min

DHT_PIN        = 4
I2C_SDA        = 21
I2C_SCL        = 22
BH1750_ADDR    = 0x23

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
def read_dht():
    # DHT22: needs >=2s between measurements (handled by deepsleep cycle)
    sensor = dht.DHT22(Pin(DHT_PIN))
    sensor.measure()
    temp = sensor.temperature()
    hum  = sensor.humidity()
    print(f"DHT22 temp: {temp:.1f}C, hum: {hum:.1f}%")
    return round(temp, 1), round(hum, 1)

def read_light():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=100000)
    sensor = BH1750(i2c, addr=BH1750_ADDR)
    lux = sensor.read_lux()
    print(f"BH1750 light: {lux:.1f} lx")
    return round(lux, 1)

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
    t = time.localtime(time.time() + 9 * 3600)  # KST
    return "rdg-{}-{:04d}{:02d}{:02d}T{:02d}{:02d}{:02d}".format(
        DEVICE_ID, t[0], t[1], t[2], t[3], t[4], t[5]
    )

def make_payload(temperature_c, humidity_pct, light_lux):
    return ujson.dumps({
        "reading_id": get_reading_id(),
        "device_id": DEVICE_ID,
        "plant_id": PLANT_ID,
        "measured_at": get_timestamp(),
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "light_lux": light_lux
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
temperature_c, humidity_pct = read_dht()
light_lux = read_light()

# build payload + local backup (always saved)
payload = make_payload(temperature_c, humidity_pct, light_lux)
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
