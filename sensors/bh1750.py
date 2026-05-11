"""
BH1750 module
I2C communication, address 0x23
"""
import board
import busio
import adafruit_bh1750


class BH1750Sensor:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.bh1750 = adafruit_bh1750.BH1750(i2c)

    def read(self):
        """
        return illuminance value (단위: lux)
        failure case None
        """
        try:
            return self.bh1750.lux
        except Exception as e:
            print(f"[BH1750] exeception: {e}")
            return None


# test code
if __name__ == "__main__":
    import time
    
    print("BH1750 test")
    sensor = BH1750Sensor()
    
    try:
        while True:
            light = sensor.read()
            if light is not None:
                print(f"illuminance: {light:.1f} lux")
            else:
                print("measurement failure")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\ncleanup")
