import json, os
from SI7021 import SI7021
from machine import I2C
from time import sleep


i2c = I2C(1)
si7021 = SI7021(i2c)


while True:
    temperature = (round(si7021.temperature(), 2))
    print(temperature)
    sleep(1)
    