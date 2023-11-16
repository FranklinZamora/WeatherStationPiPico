from micropyGPS import MicropyGPS
import time, machine

# Setup the connection to your GPS here
# This example uses UART 3 with RX on pin Y10
# Baudrate is 9600bps, with the standard 8 bits, 1 stop bit, no parity
uart = machine.UART(1, 9600)
my_gps = MicropyGPS(-7)

while True:
    
    horas, minutos, segundos = map(int, my_gps.timestamp)
    segundos = round(segundos)

    # Imprimir la hora formateada
    
    my_gps.local_offset
    sentence = uart.readline()
    if sentence:
        for x in sentence:
            my_gps.update(chr(x))
            
    timeUTC = '{:02d}:{:02d}:{:02d}'.format(horas, minutos, segundos)
    print("Hora " + timeUTC)
    print("Fecha: " + str(my_gps.date))
    print("Satelites: " + str(my_gps.satellites_in_use))
    print("Altura: " + str(my_gps.altitude))
    print(uart.read())
    print("---------------------------------------------------------")
    time.sleep(1)

