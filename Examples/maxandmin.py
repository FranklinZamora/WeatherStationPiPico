import time, machine, math, binascii, os, json, micropython, gc
from machine import I2C, UART, Pin
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button
from micropyGPS import MicropyGPS

#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))
mpl = MPL3115A2(i2cmpl, mode=MPL3115A2.ALTITUDE)
mpl2 = MPL3115A2(i2cmpl, mode=MPL3115A2.PRESSURE)

#Inicio GPS
gps = machine.UART(1, 9600)
my_gps = MicropyGPS(-7)

# Nombre del archivo de texto donde se guardarán los valores del sensor
filename = "datos.json"



#Borrado de contenido
def eraser():
    with open(filename, "w") as f:
        pass
    
# Función para obtener la hora actual
def get_current_time():
    current_time = utime.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])
    
def leer_maxmin():
    
    
    with open(filename, "r") as file:
        json_content = file.read()
        
    # Convertir el contenido del archivo en una lista de objetos Python
    data_list = json_content.strip().split('\n')
    data_objects = [json.loads(line) for line in data_list]

    #Historicos Temperatura
    max_temperature = max([obj['Temperatura'] for obj in data_objects])
    min_temperature = min([obj['Temperatura'] for obj in data_objects])
    for obj in data_objects:
        if obj['Temperatura'] == max_temperature:
            max_timeTe = obj['|']
            pass
        if obj['Temperatura'] == min_temperature:
            min_timeTe = obj['|']
            pass
            
    print('(Temperatura)', '||', max_timeTe, 'Maximo:', max_temperature, '||',min_timeTe, 'Minimo:', min_temperature)
    
    #Historicos Humedad
    max_humidity = max([obj['Humedad'] for obj in data_objects])
    min_humidity = min([obj['Humedad'] for obj in data_objects])
    for obj in data_objects:
        if obj['Humedad'] == max_humidity:
            max_timeHu = obj['|']
            pass
        if obj['Humedad'] == min_humidity:
            min_timeHu = obj['|']
            pass
    print('(Humedad)','||', max_timeHu, 'Maximo:', max_humidity, '||', min_timeHu, 'Minimo:', min_humidity)
    
    
    #Historicos Altitud
    max_alture = max([obj['Altura'] for obj in data_objects])
    min_alture = min([obj['Altura'] for obj in data_objects])
    for obj in data_objects:
        if obj['Altura'] == max_alture:
            max_timeAl = obj['|']
            pass
        if obj['Altura'] == min_alture:
            min_timeAl = obj['|']
            pass
    print('(Altura)', '||', max_timeAl, 'Maximo:', max_alture , '||', min_timeAl, 'Minimo:', min_alture)
    
    #Historicos Presion
    max_presion = max([obj['Presion'] for obj in data_objects])
    min_presion = min([obj['Presion'] for obj in data_objects])
    for obj in data_objects:
        if obj['Presion'] == max_presion:
            max_timePr = obj['|']
            pass
        if obj['Presion'] == min_presion:
            min_timePr = obj['|']
            pass
    print('(Presion)', '||', max_timePr, 'Maximo:', max_presion, '||', min_timePr, 'Minimo:', min_presion)
    
    #Historicos Lux
    max_lux = max([obj['Lux'] for obj in data_objects])
    min_lux = min([obj['Lux'] for obj in data_objects])
    for obj in data_objects:
        if obj['Lux'] == max_lux:
            max_timeLx = obj['|']
            pass
        if obj['Lux'] == min_lux:
            min_timeLx = obj['|']
            pass
    print('(Lux)', '||', max_timeLx, 'Maximo:', max_lux, '||', min_timeLx, 'Minimo:', min_lux)
    
    max_Rain = max([obj['Lluvia'] for obj in data_objects])
    min_Rain = min([obj['Lluvia'] for obj in data_objects])
    for obj in data_objects:
        if obj['Lluvia'] == max_Rain:
            max_timeRG = obj['|']
            pass
        if obj['Lluvia'] == min_Rain:
            min_timeRG = obj['|']
            pass
    print('(Lluvia)', '||', max_timeRG, 'Maximo:', max_Rain, '||', min_timeRG, 'Minimo:', min_Rain)
    
    
    
#eraser()
    
while True:
    
    
    #Offset UTC-7
    my_gps.local_offset
    
    #Formato Fecha y hora
    horas, minutos, segundos = map(int, my_gps.timestamp)
    segundos = round(segundos)
    dia, mes, anio = map(int, my_gps.date)
    
    my_gps.satellite_data_updated()
    
    #Lectura de datos GPS
    sentence = gps.readline()
    if sentence:
        for x in sentence:
            my_gps.update(chr(x))
    
    timeUTC = '{:02d}:{:02d}:{:02d}'.format(horas, minutos, segundos)
    dateNew = '{:02d}-{:02d}-{:02d}'.format(dia, mes, anio)
    
    # Obtener la hora actual
    timestamp = dateNew + " " + timeUTC
    
    #Luz ADC
    sensor_luz = machine.ADC(26)
    eficacia_luz = 90
    reading = sensor_luz.read_u16()
    corriente = (reading / 10000)
    
    #Rain Drop sensor Start
    raindrop = machine.ADC(28)
    rain_status = ''
    rain_drop = raindrop.read_u16()
    if rain_drop >= 51000:
        rainIf = 'False'
        count = 0.0
            
    elif rain_drop <= 50000:
        rainIf = 'True'
    #Sensor wind dir
    
    #Valor Sensores
    sensor_lum = (round(corriente * eficacia_luz, 2))
    sensor_temp = (round(si7021.temperature(), 2))
    sensor_hum = (round(si7021.humidity(), 2))
    sensor_alt = (round(mpl.altitude()/1000, 2))
    sensor_pres = mpl2.pressure()

    # Crear un diccionario con los datos del sensor y la hora actual
    data = {"|": timestamp, "Temperatura": sensor_temp, "Humedad": sensor_hum, "Altura": sensor_alt, "Presion": sensor_pres, "Lux": sensor_lum, "Lluvia": rainIf}
    
    
    # Abrir el archivo en modo escritura y agregar los datos al final del archivo
    with open(filename, "a") as f:
        # Serializar el diccionario a formato JSON y escribirlo en el archivo
        f.write(json.dumps(data))
        f.write("\n")
    
    print(str(gc.mem_free()))
    print(str(gc.mem_alloc()))
    micropython.alloc_emergency_exception_buf(100)
    
    gc.collect()

    leer_maxmin()
        
    print("--------------------------------------------------------------------------------------------------")
    
    time.sleep(1)






