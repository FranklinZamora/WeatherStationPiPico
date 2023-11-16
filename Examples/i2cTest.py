import machine

# Create I2C object
i2c = machine.I2C(1, scl=machine.Pin(7), sda=machine.Pin(6))

# Print out any addresses found
devices = i2c.scan()

if devices:
    for d in devices:
        print(hex(d))
