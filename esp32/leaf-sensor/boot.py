# esp32-leaf-01
# booting code

import os
import network
import socket
import time
import machine
import esp32
from machine import Pin, PWM, Timer

# config
AP_NAME        = "Sunshine-Leaf-Setup"
BUTTON_PIN     = 32
LONG_PRESS_MS  = 3000
DEBOUNCE_MS    = 50
LED_PIN        = 2
LED_BRIGHTNESS = 204  # 20% (0~1023)
LED_BLINK_MS   = 300

# LED
led = PWM(Pin(LED_PIN))
led.freq(1000)

_led_timer = Timer(0)
_led_state = False

def _led_toggle(t):
    global _led_state
    _led_state = not _led_state
    led.duty(LED_BRIGHTNESS if _led_state else 0)

def led_blink():
    global _led_state
    _led_state = False
    led.duty(0)
    _led_timer.init(period=LED_BLINK_MS, mode=Timer.PERIODIC, callback=_led_toggle)

def led_off():
    _led_timer.deinit()
    led.duty(0)

# BUTTON
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

_btn_press_ms    = 0
_btn_release_ms  = 0
_btn_event       = False
_btn_last_irq_ms = 0

def button_isr(pin):
    global _btn_press_ms, _btn_release_ms, _btn_event, _btn_last_irq_ms
    now = time.ticks_ms()

    # debounce
    if time.ticks_diff(now, _btn_last_irq_ms) < DEBOUNCE_MS:
        return
    _btn_last_irq_ms = now
    if pin.value() == 0:
        _btn_press_ms = now
    else:
        if _btn_press_ms > 0:
            _btn_release_ms = now
            _btn_event = True

def check_button():
    global _btn_event
    if not _btn_event:
        return
    _btn_event = False
    duration_ms = time.ticks_diff(_btn_release_ms, _btn_press_ms)
    handle_button(duration_ms)

def handle_button(duration_ms):
    if duration_ms >= LONG_PRESS_MS:
        print("Long press → Wi-Fi reset")
        try:
            os.remove("wifi.txt")
            print("wifi.txt deleted")
        except OSError:
            pass
        start_captive_portal()

button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=button_isr)

# Wi-Fi
def load_wifi():
    try:
        with open("wifi.txt", "r") as f:
            lines = f.read().split("\n")
            ssid = lines[0]
            password = lines[1] if len(lines) > 1 else ""
            return ssid, password
    except OSError:
        return None, None

def save_wifi(ssid, password):
    with open("wifi.txt", "w") as f:
        f.write(f"{ssid}\n{password}")
    print(f"Save wifi: {ssid}")

def url_decode(s):
    result = ""
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            result += chr(int(s[i+1:i+3], 16))
            i += 3
        else:
            result += s[i]
            i += 1
    return result

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(2)

    led_blink()

    last_attempt_ms = 0
    start_ms = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_ms) < 25000:
        if wlan.isconnected() and wlan.ifconfig()[0] != '0.0.0.0':
            led_off()
            print(f"Wi-Fi connected! IP: {wlan.ifconfig()[0]}")
            return

        # (re)connect every 5s if not actively connecting
        if wlan.status() != network.STAT_CONNECTING:
            if time.ticks_diff(time.ticks_ms(), last_attempt_ms) > 5000:
                print(f"Status {wlan.status()} → (re)connect")
                try:
                    wlan.connect(ssid, password) if password else wlan.connect(ssid)
                except OSError as e:
                    print(f"Connect error: {e}")
                last_attempt_ms = time.ticks_ms()

        time.sleep(0.5)

    # fallback: 5min deepsleep (auto recovery, no captive portal)
    led_off()
    print("Connection failed → deepsleep 5min")
    esp32.wake_on_ext0(pin=Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP), level=0)
    machine.deepsleep(5 * 60 * 1000)

def start_captive_portal():
    button.irq(handler=None)

    sta = network.WLAN(network.STA_IF)
    if sta.active():
        sta.active(False)

    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    # open AP (no password)
    ap.config(essid=AP_NAME, authmode=0)
    print(f"AP start: {AP_NAME}")

    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dns.bind(("0.0.0.0", 53))
    dns.setblocking(False)

    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen(5)
    s.setblocking(False)

    HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sunshine Setup</title>
    <style>
        body { font-family: Verdana; text-align: center; padding: 20px; }
        input { width: 80%; padding: 10px; margin: 10px; font-size: 16px; }
        button { width: 80%; padding: 10px; background: #4CAF50; color: white; font-size: 16px; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>🌱 Sunshine Wi-Fi Setting</h2>
    <form method="POST" action="/">
        <p><input name="ssid" type="text" placeholder="Wi-Fi name"></p>
        <p><input name="password" type="password" placeholder="password"></p>
        <p><button type="submit">submit</button></p>
    </form>
</body>
</html>"""

    led_blink()

    while True:
        # DNS
        try:
            data, addr = dns.recvfrom(512)
            response  = data[:2] + b'\x81\x80' + data[4:6] + data[4:6]
            response += b'\x00\x00\x00\x00'
            response += data[12:]
            response += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
            response += bytes([192, 168, 4, 1])
            dns.sendto(response, addr)
        except OSError:
            pass

        # HTTP
        try:
            conn, addr = s.accept()
            request = conn.recv(1024)

            if b"POST" in request:
                body = request.split(b"\r\n\r\n")[1].decode()
                params = {}
                for param in body.split("&"):
                    if "=" in param:
                        k, v = param.split("=", 1)
                        params[k] = v.replace("+", " ")

                ssid = url_decode(params.get("ssid", ""))
                password = url_decode(params.get("password", ""))

                if ssid:
                    save_wifi(ssid, password)
                    conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                    conn.send("<h2>Save complete! Restarting...</h2>".encode())
                    conn.close()
                    time.sleep(2)
                    machine.reset()
            else:
                conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                conn.send(HTML.encode())
                conn.close()
        except OSError:
            pass

        time.sleep(0.02)

# RUN

# boot-time long-press check (Wi-Fi reset shortcut at any time)
held_ms = 0
while button.value() == 0:
    time.sleep_ms(100)
    held_ms += 100
    if held_ms >= LONG_PRESS_MS:
        print("Long press at boot → Wi-Fi reset")
        try:
            os.remove("wifi.txt")
        except OSError:
            pass
        start_captive_portal()

ssid, password = load_wifi()
if ssid:
    print(f"Saved Wi-Fi: {ssid}")
    connect_wifi(ssid, password)
else:
    print("No Wi-Fi info → captive portal")
    start_captive_portal()
