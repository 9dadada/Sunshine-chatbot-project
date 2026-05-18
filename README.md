# Sunshine — AI-Powered Plant Care Chatbot

An IoT-based plant care app where users insert sensors into their pots and register a plant photo.
The AI automatically identifies the plant species and provides real-time environment data and personalized care guides via chatbot.

## System Architecture

```
[Pot + Sensor Node] → [MQTT Broker] → [Backend Server] → [User App]
   Sensor Reading      Message Relay   DB + RAG           Chatbot + Graph
```

This repository hosts the **sensor node** firmware in two parallel implementations on different hardware platforms.

---

## Implementations

| Folder | Platform | Status | Description |
|---|---|---|---|
| [`raspberry-pi/`](raspberry-pi/) | Raspberry Pi 4 + Python | Full-feature reference | Initial implementation. Used to validate the end-to-end pipeline before moving to a wireless-friendly board. |
| [`esp32/`](esp32/) | ESP32 + MicroPython | Field-deployable prototype | Battery-powered, deep-sleep, captive-portal Wi-Fi setup. The target hardware going forward. |

Both implementations measure the same plant environment (soil moisture / temperature / humidity / light) and publish over MQTT to the same backend.

---

## Why Two Implementations?

The Raspberry Pi version was built first because wireless Wi-Fi onboarding was **not in the MVP scope** — we needed to validate that the full sensor → MQTT → backend pipeline worked end to end. Once that was confirmed, the work moved to ESP32 to gain:

- **Battery operation** with deep-sleep between readings
- **Built-in Wi-Fi** with captive-portal onboarding (no SD card editing)
- **Smaller form factor** and lower BOM cost for the actual product

The Raspberry Pi code is preserved as a reference implementation and for environments where a full Linux stack is preferable.

---

## Sensors (Common Spec)

| Sensor | Measurement |
|---|---|
| DHT22 | Temperature / Humidity |
| BH1750 GY-302 | Light |
| Capacitive Soil Moisture Sensor v2.0 | Soil Moisture |

Wiring and per-platform details live in each subfolder's README.

---

## Getting Started

Pick the platform you want to deploy on:

- **Raspberry Pi** → [`raspberry-pi/README.md`](raspberry-pi/README.md)
- **ESP32** → [`esp32/README.md`](esp32/README.md)
