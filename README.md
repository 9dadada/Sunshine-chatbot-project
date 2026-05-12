# Sunshine — AI-Powered Plant Care Chatbot

A IoT-based plant care app where users insert sensors into their pots and register a plant photo.  
The AI automatically identifies the plant species and provides real-time environment data and personalized care guides via chatbot.

## System Architecture
[Pot + Raspberry Pi] → [MQTT Broker] → [Backend Server] → [User App]
Sensor Reading        Message Relay    DB + RAG           Chatbot + Graph

---

## This Repository

This repo covers the **Raspberry Pi sensor node** part of the system.  
It measures the plant environment every 5 minutes and publishes the data to the backend via MQTT.

---

## Sensors

| Sensor | Measurement | Connection |
|--------|------------|------------|
| DHT22 | Temperature / Humidity | GPIO 4 |
| BH1750 GY-302 | Light | I2C (0x23) |
| Capacitive Soil Moisture Sensor v2.0 | Soil Moisture | SPI (MCP3008 CH0) |

---

## Project Structure
```
plant_project/
├── config.py          
├── main.py            
├── measurement.py     
├── mqtt_client.py     
├── sensors/
│   ├── dht22.py
│   ├── bh1750.py
│   └── soil_humid.py
└── requirements.txt
```
---

## Getting Started

```bash
# Activate virtual environment
source .venv/bin/activate

# Run
python main.py
```

---

## MQTT Payload

```json
{
  "reading_id": "rdg-rpi-edge-node-01-20260508T163045",
  "device_id": "rpi-edge-node-01",
  "plant_id": "plant-001",
  "measured_at": "2026-05-08T16:30:45+09:00",
  "temperature_c": 24.5,
  "humidity_pct": 55.2,
  "light_lux": 850.0,
  "soil_moisture_pct": 42.0
}
```

- **Broker**: `broker.hivemq.com:1883` (temporary)
- **Topic**: `sensor/readings/rpi-edge-node-01`
- **QoS**: 1


