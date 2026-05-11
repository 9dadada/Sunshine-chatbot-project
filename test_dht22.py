import time
import board
import adafruit_dht

dht = adafruit_dht.DHT22(board.D4)

while True:
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        print(f"온도: {temperature:.1f}°C, 습도: {humidity:.1f}%")
    except RuntimeError as e:
        print(f"재시도: {e}")
    time.sleep(2)

