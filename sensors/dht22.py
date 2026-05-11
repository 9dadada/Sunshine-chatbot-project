"""
DHT22 module
GPIO 4 (Pin 7)
"""
import board
import adafruit_dht


class DHT22Sensor:
    def __init__(self, pin=board.D4):
        self.dht = adafruit_dht.DHT22(pin)

    def read(self):
        """
        measurement value: (temperature, humidity)
        fail (None, None)
        """
        try:
            return self.dht.temperature, self.dht.humidity
        except RuntimeError:
            return None, None
        except Exception as e:
            print(f"[DHT22] exception: {e}")
            return None, None

    def cleanup(self):
        try:
            self.dht.exit()
        except Exception:
            pass


# test code
if __name__ == "__main__":
    import time
    
    print("DHT22 module test")
    sensor = DHT22Sensor()
    
    try:
        while True:
            temp, hum = sensor.read()
            if temp is not None:
                print(f"temperature: {temp:.1f}°C  |  humidity: {hum:.1f}%")
            else:
                print("measurement failure (Retrying...)")
            time.sleep(2)
    except KeyboardInterrupt:
        sensor.cleanup()
        print("\cleanup")
