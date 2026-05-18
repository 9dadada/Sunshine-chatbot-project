# esp32-soil-01
# boot.py

import os
import network
import socket
import time
import machine
import esp32
from machine import Pin, PWM, Timer, deepsleep, wake_reason, EXT0_WAKE

# ── config ────────────────────────────────────────────────────────────────────
AP_NAME        = "Sunshine-Soil-Setup"
BUTTON_PIN     = 32
LONG_PRESS_MS  = 3000
DEBOUNCE_MS    = 50
LED_PIN        = 2
LED_BRIGHTNESS = 204  # 20% (0~1023)
LED_BLINK_MS   = 300

# ── LED ───────────────────────────────────────────────────────────────────────
# led_blink()로 비동기 깜빡임 시작 → 하드웨어 타이머가 LED_BLINK_MS마다 자동 토글.
# led_on() / led_off() 호출 시 타이머가 자동 정지되어 상태가 고정됨.
led = PWM(Pin(LED_PIN))
led.freq(1000)

_led_timer = Timer(0)
_led_state = False

def _led_toggle(t):
    # 타이머 콜백 = ISR 컨텍스트. 메모리 할당/print 금지. 전역 토글만.
    global _led_state
    _led_state = not _led_state
    led.duty(LED_BRIGHTNESS if _led_state else 0)

def led_blink():
    global _led_state
    _led_state = False
    led.duty(0)
    _led_timer.init(period=LED_BLINK_MS, mode=Timer.PERIODIC, callback=_led_toggle)

def led_on():
    _led_timer.deinit()
    led.duty(LED_BRIGHTNESS)

def led_off():
    _led_timer.deinit()
    led.duty(0)

# ── button ────────────────────────────────────────────────────────────────────
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# ISR은 "시간 기록 + 플래그" 만. 실제 작업은 메인 컨텍스트의 check_button()에서.
# MicroPython ISR 규칙:
#   - 메모리 할당 금지 (객체 생성, 문자열 연산, print 등)
#   - 파일/소켓 I/O 금지
#   - try/except 사용 금지 (예외 발생 시 시스템 정지)
# → 이 규칙을 어기면 무작위 MemoryError 또는 시스템 행이 발생함.
_btn_press_ms    = 0
_btn_release_ms  = 0
_btn_event       = False
_btn_last_irq_ms = 0

def button_isr(pin):
    global _btn_press_ms, _btn_release_ms, _btn_event, _btn_last_irq_ms
    now = time.ticks_ms()
    # 디바운싱: 기계식 버튼은 누를 때 수 ms 동안 채터링(여러 번 ON/OFF) 발생.
    # 직전 IRQ로부터 DEBOUNCE_MS 이내에 또 들어온 신호는 노이즈로 간주.
    if time.ticks_diff(now, _btn_last_irq_ms) < DEBOUNCE_MS:
        return
    _btn_last_irq_ms = now
    if pin.value() == 0:
        _btn_press_ms = now
    else:
        if _btn_press_ms > 0:
            _btn_release_ms = now
            _btn_event = True   # 메인 루프가 처리하도록 플래그만 세팅

def check_button():
    """메인 루프(또는 안전한 컨텍스트)에서 호출. ISR이 남긴 이벤트를 처리한다."""
    global _btn_event
    if not _btn_event:
        return
    _btn_event = False
    duration_ms = time.ticks_diff(_btn_release_ms, _btn_press_ms)
    handle_button(duration_ms)

def handle_button(duration_ms):
    if duration_ms >= LONG_PRESS_MS:
        # 길게 → Wi-Fi 재설정
        print("Long press → Wi-Fi reset")
        try:
            os.remove("wifi.txt")
            print("wifi.txt deleted")
        except OSError:
            pass
        start_captive_portal()
    else:
        # 짧게 → 딥슬립
        print("Short press → deepsleep")
        led_off()
        esp32.wake_on_ext0(pin=button, level=esp32.WAKEUP_ALL_LOW)
        deepsleep()

button.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=button_isr)

# ── Wi-Fi ─────────────────────────────────────────────────────────────────────
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

    try:
        wlan.connect(ssid, password) if password else wlan.connect(ssid)
    except OSError as e:
        print(f"Connect error: {e}")
        start_captive_portal()
        return

    # network.STAT_GOT_IP 상수 사용 이유:
    #   원래 코드의 1010은 "IP 받음" 상태를 나타내는 매직 넘버였음.
    #   MicroPython 펌웨어가 업데이트되면 내부 enum 값이 바뀔 수 있어
    #   숫자를 직접 비교하면 어느 날 갑자기 영원히 false가 되는 버그가 생김.
    #   상수명을 쓰면 펌웨어가 알아서 올바른 값을 매핑해 줌.
    led_blink()
    start_ms = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_ms) < 15000:  # 15초 대기
        if wlan.status() == network.STAT_GOT_IP and wlan.ifconfig()[0] != '0.0.0.0':
            led_on()  # 타이머 자동 중단 + LED 상시 점등
            print(f"Wi-Fi connected! IP: {wlan.ifconfig()[0]}")
            return
        check_button()    # 연결 대기 중에도 버튼 응답 유지
        time.sleep(0.02)  # CPU 양보

    print("Connection failed → captive portal")
    start_captive_portal()

def start_captive_portal():
    # 포털 진입 시 버튼 IRQ 해제 — 설정 도중 실수로 deepsleep/포털 재진입 방지.
    # 사용자가 Wi-Fi 입력 중에 버튼이 눌리면 절대 안 되므로 핸들러를 떼어 둔다.
    # (재부팅 후 boot.py가 처음부터 다시 실행되며 IRQ도 다시 붙는다.)
    button.irq(handler=None)

    # STA가 켜져 있으면 끄기 — AP와 채널 경합 및 전력 낭비 방지
    sta = network.WLAN(network.STA_IF)
    if sta.active():
        sta.active(False)

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    # authmode=0 → OPEN. 비밀번호 입력 없이 폰에서 바로 접속해 설정 페이지로 진입.
    # 보안보다 데모 UX 우선.
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

    led_blink()  # 하드웨어 타이머가 백그라운드에서 LED 깜빡임 유지

    while True:
        # DNS (non-blocking — 데이터 없으면 OSError로 즉시 빠짐)
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

        # HTTP (non-blocking)
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

        # CPU 양보 — 20ms면 LED 토글 주기(300ms) 안에 충분히 여러 번 돌면서
        # DNS/HTTP 응답성도 유지된다.
        time.sleep(0.02)

# ── run ───────────────────────────────────────────────────────────────────────
led_on()

if wake_reason() == EXT0_WAKE:
    # 딥슬립에서 깨어남 → main.py로 바로 진행
    print("Wakeup from deepsleep → main.py")
else:
    # 일반 부팅 → Wi-Fi 연결
    ssid, password = load_wifi()
    if ssid:
        print(f"Saved Wi-Fi: {ssid}")
        connect_wifi(ssid, password)
    else:
        print("No Wi-Fi info → captive portal")
        start_captive_portal()
