# ESP32 Sensor Node — `boot.py`

MicroPython firmware for the ESP32-based sensor node. Handles **boot-time
provisioning**: Wi-Fi auto-connect, captive-portal onboarding for first-time
setup, button-driven deep-sleep and Wi-Fi reset, and LED status feedback.

Sensor measurement and MQTT publishing run in `main.py` (executed by MicroPython
immediately after `boot.py` returns).

---

## User-Facing Behavior

```
[Power on or wake from deep-sleep]
        │
        ├─ Woken by button (EXT0_WAKE) ───→ skip boot, run main.py
        │
        ├─ Saved Wi-Fi found ──────────────→ try to connect (15s)
        │     ├─ Success → LED solid → main.py
        │     └─ Fail    → fall back to captive portal
        │
        └─ No saved Wi-Fi  ────────────────→ captive portal
```

**Button:**

| Press | Action |
|---|---|
| Short (< 3 s) | Enter deep-sleep. Next press wakes the device. |
| Long  (≥ 3 s) | Delete saved Wi-Fi credentials and enter captive portal. |

**LED:**

| State | Meaning |
|---|---|
| Solid on  | Booting / Wi-Fi connected |
| Blinking  | Wi-Fi connecting / captive portal active |
| Off       | Deep-sleep |

**Captive portal:**
1. Device exposes an open Wi-Fi AP named `Sunshine-Soil-Setup`.
2. Phone connects without a password.
3. Any URL the phone opens redirects to a setup page (DNS hijack to `192.168.4.1`).
4. User enters home Wi-Fi SSID and password, submits.
5. Device saves credentials to `wifi.txt`, reboots, auto-connects.

---

## Config

All tunables sit at the top of [`boot.py`](boot.py):

| Constant | Default | Meaning |
|---|---|---|
| `AP_NAME` | `Sunshine-Soil-Setup` | SSID of the setup AP |
| `BUTTON_PIN` | `32` | GPIO pin for the user button |
| `LONG_PRESS_MS` | `3000` | Long-press threshold |
| `DEBOUNCE_MS` | `50` | Button debouncing window |
| `LED_PIN` | `2` | GPIO pin for the status LED |
| `LED_BRIGHTNESS` | `204` | PWM duty 0–1023 (≈ 20 %) |
| `LED_BLINK_MS` | `300` | LED toggle period |

---

## Architecture

### LED — hardware-timer driven
- `_led_timer` (Timer 0) automatically toggles the LED every `LED_BLINK_MS`.
- `led_blink()` arms the timer (returns immediately).
- `led_on()` / `led_off()` deinit the timer **and** set the LED state in one call,
  so callers never have to remember to "stop the blink before turning solid".

### Button — ISR-safe, debounced, polled
- `button_isr(pin)` runs in interrupt context. Per MicroPython ISR rules it
  does no allocation, no `print`, no I/O — only records press/release timestamps
  and sets an event flag.
- `check_button()` is polled from the main loop (e.g. inside `connect_wifi`'s
  wait loop). It reads the flag in a safe context and dispatches to
  `handle_button(duration_ms)`, which then performs the heavy work
  (`deepsleep`, file delete, captive portal).
- 50 ms debouncing inside the ISR rejects mechanical contact bounce.

### Wi-Fi
- `load_wifi()` / `save_wifi()` persist credentials in plain `wifi.txt`.
- `connect_wifi()` activates STA, calls `wlan.connect()`, then polls for up to
  15 s. The loop uses `time.ticks_ms()` instead of a fixed iteration count, so
  changing the timeout is a one-number edit.
- Status check uses `network.STAT_GOT_IP` (not the literal `1010`) so the code
  doesn't break on a firmware upgrade.

### Captive portal
- Disables the button IRQ on entry — prevents a stray short press from killing
  the user mid-setup.
- Brings up an open AP, a non-blocking DNS server on port 53, and a non-blocking
  HTTP server on port 80.
- DNS answers every query with `192.168.4.1` so the phone's captive-portal
  detector lands on our setup page regardless of which URL it probes.
- Main loop is purely DNS + HTTP. LED blinking happens in the background via
  Timer 0, so heavy HTTP responses do not stretch the blink interval.
- A successful form POST writes `wifi.txt`, replies "Save complete!", waits 2 s,
  then `machine.reset()`. The next boot picks up the credentials and skips the
  portal.

---

## Function Reference

### LED
| Function | Purpose |
|---|---|
| `led_on()` | Stop any running blink (`_led_timer.deinit()`) and drive LED on at 20 %. |
| `led_off()` | Stop any running blink and drive LED off. |
| `led_blink()` | Start the hardware timer; LED toggles automatically every `LED_BLINK_MS`. |
| `_led_toggle(t)` | Timer callback (ISR context). Flips `_led_state` and applies it. |

### Button
| Function | Purpose |
|---|---|
| `button_isr(pin)` | Hardware IRQ handler. Records timestamps, sets event flag, debounces. |
| `check_button()` | Polled by the main loop. Consumes the event flag and dispatches. |
| `handle_button(duration_ms)` | Short → deep-sleep. Long → wipe `wifi.txt` + captive portal. |

### Wi-Fi
| Function | Purpose |
|---|---|
| `load_wifi()` | Read SSID/password from `wifi.txt`. Returns `(None, None)` if missing. |
| `save_wifi(ssid, password)` | Persist credentials to `wifi.txt`. |
| `url_decode(s)` | Decode `%XX` percent-encoding from form submissions (Korean SSID etc.). |
| `connect_wifi(ssid, password)` | Activate STA, connect, wait up to 15 s, on failure fall back to portal. |
| `start_captive_portal()` | AP + DNS + HTTP server loop. Saves credentials and reboots on form POST. |

### Measurement loop (`main.py`)
Runs immediately after `boot.py` returns. One measurement per wake cycle:
verify Wi-Fi, read the soil ADC, publish to MQTT, then deep-sleep for 5 minutes
(or until the button is pressed).

| Function | Purpose |
|---|---|
| `check_button()` | One-shot button read. Used to allow an immediate user-driven deep-sleep. |
| `go_deepsleep()` | Configure EXT0 wake on the button pin, then `deepsleep(SLEEP_MS)`. |
| `read_soil()` | 10-sample ADC read on `SOIL_PIN`, averaged and mapped to 0–100 % using `AIR_VAL` / `WATER_VAL` calibration constants. |
| `get_wlan()` | Return the active STA WLAN if it has an IP; otherwise `None`. |
| `get_timestamp()` / `get_reading_id()` | Build the ISO-8601 timestamp and a unique `reading_id` for the MQTT payload. |
| `publish(soil_moisture_pct)` | Connect to the MQTT broker, publish a JSON reading, disconnect. |

---

## Flashing

1. Flash MicroPython onto the ESP32 (see [docs.micropython.org/en/latest/esp32/tutorial/intro.html](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html)).
2. Copy `boot.py` and `main.py` to the device root with `mpremote` or Thonny:
   ```
   mpremote cp boot.py :boot.py
   mpremote cp main.py :main.py
   ```
3. Reset the device. On first boot the LED blinks and the captive portal comes up;
   on subsequent boots it auto-connects to the saved network and `main.py` takes over.

---

## Known Limitations

- AP is **open** (no WPA2). Anyone in Wi-Fi range during the setup window can
  connect. We accept this for the MVP because it matches common consumer-IoT
  setup UX and dramatically simplifies the user flow. Closing it requires
  shipping a per-device password printed on the case.
- `wifi.txt` stores the home Wi-Fi password in plain text. A flash dump exposes
  it. Acceptable for prototype, would need on-device encryption for production.
- HTTP receive buffer is fixed at 1024 bytes. Korean SSIDs URL-encode to ~9 bytes
  per character, so very long Korean SSIDs (≳ 30 characters) plus large request
  headers can be truncated. Loop-based recv would lift this limit.
