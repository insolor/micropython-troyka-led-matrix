from troyka_led_matrix import TroykaLedMatrix
from urandom import getrandbits
import time

matrix = TroykaLedMatrix()

while True:
    matrix.draw_pixel(getrandbits(3), getrandbits(3))
    matrix.clear_pixel(getrandbits(3), getrandbits(3))
    time.sleep_ms(50)
