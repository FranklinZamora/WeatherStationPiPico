import utime, machine, math, binascii, os, json, micropython, gc
from machine import I2C, UART, Pin
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button
from micropyGPS import MicropyGPS
import ustruct
from micropyGPS import MicropyGPS
import time, machine

uart = machine.UART(1, 115200)
my_gps = MicropyGPS(-7)

#Wind speed and Bucket size
wind_count = 0
radius_cm = 9.0
wind_interval = 1
CmInAnHour = 100000.0
SecsInAnHour = 3600
Adjustment = 1.18
BUCKET_SIZE = 0.2794
count = 0

#uart
gps = machine.UART(1, 115200)
my_gps = MicropyGPS()

#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))

#lenght bytes
frame = bytearray(20)


def GPS():
    sentence = uart.readline()
    if sentence:
        for x in sentence:
            my_gps.update(chr(x))

    # Obtener la hora, minutos y segundos correctamente
    horas, minutos, segundos = my_gps.timestamp
    segundos = round(segundos)
    
    # Obtener la fecha correctamente
    ano, mes, dia = my_gps.date

    # Imprimir la hora formateada
    timeUTC = '{:02d}:{:02d}:{:02d}'.format(horas, minutos, segundos)
    dateNew = '{:04d}-{:02d}-{:02d}'.format(ano, mes, dia)
    
    #datos crudo del GPS
#     print("Date: " + dateNew + " " + timeUTC)
#     print("Satelites: " + str(my_gps.satellites_in_use))
#     print (str(my_gps.date))
#     print(uart.read())
#     print("---------------------------------------------------------")
    time.sleep(1)
    return horas, minutos, segundos

#Metod Rain
def bucket_tipped():                             
    global count
    count += 1

#Metods Wind Speed
def spin():                                      
    global wind_count
    wind_count += 1
    
def calculate_speed(time_sec):
    global wind_count
    circunferencia_cm = (2 * math.pi) * radius_cm
    rotaciones = wind_count / 2.0
    dist_km = (circunferencia_cm * rotaciones) / CmInAnHour
    kmpersec = dist_km / time_sec
    kmperhour = kmpersec * SecsInAnHour
    return kmperhour * Adjustment
speed = Button(9)
speed.when_activated = spin

def get_historicals():
    try:
        # Intenta leer el diccionario de contadores desde la memoria flash
        with open('/Max_min.txt', 'r') as file:
            contadores = eval(file.read())        

    except (OSError, SyntaxError):
        contadores = {
            "Maximo temperatura": 0,
            "Maximo humedad": 0,
            "Maximo presion": 0,
            "Maximo luz": 0,
            "Maximo lluvia": 0,
            "Maximo viento": 0,
            "Minimo temperatura": 1000000000,
            "Minimo humedad": 1000000000,
            "Minimo presion": 1000000000,
            "Minimo luz": 1000000000,
            "Minimo lluvia": 1000000000,
            "Minimo viento": 1000000000,
            "Tiempo Maximo temperatura": 0,
            "Tiempo Maximo humedad": 0,
            "Tiempo Maximo presion": 0,
            "Tiempo Maximo luz": 0,
            "Tiempo Maximo lluvia": 0,
            "Tiempo Maximo viento": 0,
            "Tiempo Minimo temperatura": 0,
            "Tiempo Minimo humedad": 0,
            "Tiempo Minimo presion": 0,
            "Tiempo Minimo luz": 0,
            "Tiempo Minimo lluvia": 0,
            "Tiempo Minimo viento": 0
            
        }

        # Guarda el diccionario inicial en el archivo
        with open('/Max_min.txt', 'w') as file:
            file.write(str(contadores))
 
    Max_temp = contadores.get("Maximo temperatura", 0)  
    Max_Hum = contadores.get("Maximo humedad", 0)
    Max_pressure = contadores.get("Maximo presion", 0)
    Max_ligth = contadores.get("Maximo luz", 0)
    Max_rain = contadores.get("Maximo lluvia", 0)
    Max_Speed = contadores.get("Maximo viento", 0)
    
    Min_temp = contadores.get("Minimo temperatura", 1000000000)  
    Min_Hum = contadores.get("Minimo humedad", 1000000000)
    Min_pressure = contadores.get("Minimo presion", 1000000000)
    Min_ligth = contadores.get("Minimo luz", 1000000000)
    Min_rain = contadores.get("Minimo lluvia", 1000000000)
    Min_Speed = contadores.get("Minimo viento", 1000000000)
    
    Time_Max_temp = contadores.get("Tiempo Maximo temperatura", 0)  
    Time_Max_Hum = contadores.get("Tiempo Maximo humedad", 0)
    Time_Max_pressure = contadores.get("Tiempo Maximo presion", 0)
    Time_Max_ligth = contadores.get("Tiempo Maximo luz", 0)
    Time_Max_rain = contadores.get("Tiempo Maximo lluvia", 0)
    Time_Max_Speed = contadores.get("Tiempo Maximo viento", 0)
    
    Time_Min_temp = contadores.get("Tiempo Minimo temperatura", 0)  
    Time_Min_Hum = contadores.get("Tiempo Minimo humedad", 0)
    Time_Min_pressure = contadores.get("Tiempo Minimo presion", 0)
    Time_Min_ligth = contadores.get("Tiempo Minimo luz", 0)
    Time_Min_rain = contadores.get("Tiempo Minimo lluvia", 0)
    Time_Min_Speed = contadores.get("Tiempo Minimo viento", 0)
    
    
    return (
        Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
        Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
        Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
        Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed
            )
    
def Change_historical(Sensor_name,Sensor_data,Sensor_time,time):
    try:
        with open('/Max_min.txt', 'r') as file:
            historical = eval(file.read())
            #print("mis ", Sensor_name ,historical)
        
        historical[Sensor_name] = Sensor_data
        with open('/Max_min.txt', 'w') as file:
            file.write(str(historical))
            
        historical[Sensor_time] = time
        with open('/Max_min.txt', 'w') as file:
            file.write(str(historical))

    except (OSError, SyntaxError):
        # Si el archivo no existe o no es un diccionario válido, iniciar con un diccionario vacío
        historical = {}

(
    Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
    Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
    Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
    Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed
 ) = get_historicals()

while True:
    
    
    GPS()
    hora,minutos,segundos =  GPS()
    timeUTC = '{:02d}:{:02d}:{:02d}'.format(hora, minutos, segundos)
    #print("mi hora",hora , "min" , minutos , "segundos",segundos)
    
    #Wind direccion
    wind_dir = machine.ADC(27)
    dir_wind = ""
    wind = round((wind_dir.read_u16() * 3.3) / 1000, 1)
    wind_directions = [
        ("NORTE", 189.2, 194.8),
        ("ESTE", 83.4, 86.91),
        ("SUR", 119.8, 126.2),
        ("OESTE", 205.5, 210.9),
        ("NE", 147.7, 151.4),
        ("NNE", 136.3, 143.5),
        ("ESE", 78.2, 85.2),
        ("SE", 101.1, 109.0),
        ("SSE", 90.5, 96.2),
        ("SSO", 112.5, 116.8),
        ("SO", 170.3, 177.8),
        ("OSO", 167.0, 169.6),
        ("OSO", 167.0, 169.6),
        ("ONO", 194.5, 197.1),
        ("NO", 201.6, 205.4),
        ("NO", 180.7, 201.3),
        ]

    # Inicializa la dirección del viento como vacía
    dir_wind = ""

    # Itera sobre los rangos y asigna la dirección del viento
    for direction, lower, upper in wind_directions:
        if lower <= wind <= upper:
            dir_wind = direction
            break
        
    #rain sensor
    rain_sensor = Button(8)
    rain_sensor.when_pressed = bucket_tipped
    rain = count * BUCKET_SIZE
    str_rain = str(rain)
    str_pRain = str_rain + 'mm/'
    rain_data = (int(rain*100))
    rain_bytes = ustruct.pack('H', rain_data)
    #print(str_pRain)
        
    #Speed Wind sensor Start       
    wind_count = 0
    time.sleep(wind_interval)
    spdCstr = str(calculate_speed(wind_interval))
    speedC = spdCstr + 'Kmh/'
    speedReal = calculate_speed(wind_interval)
   # print(speedReal)
    SpeedReal_ = (int(speedReal*100))
    Speed_bytes = ustruct.pack('H', SpeedReal_)
    
    #Altura
    mpl = MPL3115A2(i2cmpl, mode=MPL3115A2.ALTITUDE) 
    alt = int((mpl.altitude() * -1) * 100)
    altBytes = ustruct.pack('H', alt)
    #print("Altura", alt)
        
    #dir wind
    dir_wind_ = (int(wind*100))
    dir_wind_Bytes = ustruct.pack('H', dir_wind_)
    
    #temperature °C
    temperature = (int(si7021.temperature()) * 100)
    tempCBytes = ustruct.pack('H', temperature)
    
    #temperature °F
    temperatureF = int((si7021.temperature() * 9/5 + 32) * 100)
    tempFBytes = ustruct.pack('H',temperatureF)
    
    #humity
    humidity = int(si7021.humidity() * 100)
    humBytes = ustruct.pack('H', humidity)
    
    #Ligth
    sensor_luz = machine.ADC(26)
    eficacia_luz = 90
    reading = sensor_luz.read_u16()
    corriente = (reading / 10000)
    lum = int((corriente * eficacia_luz)*100)
    lumBytes = ustruct.pack('H',lum)
    
    #pressure
    mpl2 = MPL3115A2(i2cmpl, mode=MPL3115A2.PRESSURE)
    sensor_pres = mpl2.pressure()
    pressure =  int((sensor_pres)*100)
    pressureBytes = ustruct.pack('I',pressure)
    
    
    #Speed Wind sensor Start
    
    wind_count = 0
    time.sleep(wind_interval)
    spdCstr = str(calculate_speed(wind_interval))
    speedC = spdCstr + 'Kmh/'
    
#     print("Longitud de pressureBytes:", len(pressureBytes))
    
    #frames HEX message 
    frame[0] = tempCBytes[1]
    frame[1] = tempCBytes[0]
    frame[2] = tempFBytes[1]
    frame[3] = tempFBytes[0]
    frame[4] = humBytes[1]
    frame[5] = humBytes[0]          
    frame[6] = lumBytes[1]
    frame[7] = lumBytes[0]
    frame[8] = pressureBytes[3]
    frame[9] = pressureBytes[2]
    frame[10] = pressureBytes[1]
    frame[11] = pressureBytes[0]
    frame[12] = dir_wind_Bytes[1]
    frame[13] = dir_wind_Bytes[0]
    frame[14] = Speed_bytes[1]
    frame[15] = Speed_bytes[0]
    frame[16] = altBytes[1]
    frame[17] = altBytes[0]
    frame[18] = rain_bytes[1]
    frame[19] = rain_bytes[0]
    
  
    
    #Show message
#     for i in range(0,18):
#         print(hex(frame[i]), end = ' ')
#         
#     print('\n')
#     print("Presion Barometrica", sensor_pres)
#     print('\n')
    
#     #Historicals MAX
    if temperature > Max_temp:      
        Change_historical("Maximo temperatura", temperature,"Tiempo Maximo temperatura",timeUTC)
        print("New historical:", temperature)
        historicals = get_historicals()
#         Max_temp = historicals[0]
#         Time_Max_temp = historicals[12]
#         print("max temp" , Max_temp )
#         print("TIME max temp" , Time_Max_temp )
        
    if humidity > Max_Hum:
        Change_historical("Maximo humedad" , humidity ,"Tiempo Maximo humedad", timeUTC )
        historicals = get_historicals()
#         Max_Hum = historicals[1]
#         Time_Max_Hum = historicals[13]
#         print("max hum" , Max_Hum )
#         print("TIME max hum" , Time_Max_Hum )
        
    if pressure > Max_pressure:
        Change_historical("Maximo presion" , pressure,"Tiempo Maximo presion",timeUTC)
        print("New historical:", pressure)
        historicals = get_historicals()
#         Max_pressure = historicals[2]
#         Time_Max_pressure = historicals[14]
#         print("max Max_pressure" , Max_pressure )
#         print("TIME max Time_Max_pressure" , Time_Max_pressure )
               
    if lum > Max_ligth:
        Change_historical("Maximo luz", lum,"Tiempo Maximo luz",timeUTC)
        historicals = get_historicals()
#         Max_ligth = historicals[3]
#         Time_Max_ligth = historicals[15]
#         print("max lux" , Max_ligth )
#         print("TIME max lux" , Time_Max_ligth )
     
    if rain_data > Max_rain:
        Change_historical("Maximo lluvia", rain_data, "Tiempo Maximo lluvia",timeUTC)
        historicals = get_historicals()
#         Max_rain = historicals[4]
#         Time_Max_rain = historicals[16]
#         print("max Max_rain" , Max_rain )
#         print("TIME max Time_Max_rain" , Time_Max_rain )
         
    if SpeedReal_ > Max_Speed:
        Change_historical("Maximo viento", SpeedReal_,"Tiempo Maximo viento",timeUTC)
        
#         Max_Speed = historicals[5]
#         Time_Max_Speed = historicals[17]
#         print("max Max_Speed" , Max_Speed )
#         print("TIME max Time_Max_Speed" , Time_Max_Speed )

    #Historicals MIN
    if temperature < Min_temp:
        Change_historical("Minimo temperatura" ,temperature , "Tiempo Minimo temperatura" , timeUTC )
        historicals = get_historicals()
        Min_temp = historicals[6]
        Time_Min_temp = historicals[18]
        print("Min_temp" , Min_temp )
        print("Time_Min_temp" , Time_Min_temp )
        
    if humidity < Min_Hum:
        Change_historical("Minimo humedad" , humidity ,"Tiempo Minimo humedad", timeUTC )
        historicals = get_historicals()
        Min_Hum = historicals[7]
        Time_Min_Hum = historicals[19]
        print("Min_Hum" , Min_Hum )
        print("Time_Min_Hum" , Time_Min_Hum )
        
    if pressure < Min_pressure:
        Change_historical("Minimo presion" , pressure,"Tiempo Minimo presion",timeUTC)
        print("min historical:", pressure)
        historicals = get_historicals()
        Min_pressure = historicals[8]
        Time_Min_pressure = historicals[20]
        print("Min_pressure" , Min_pressure )
        print("Time_Min_pressure" , Time_Min_pressure )
               
    if lum < Min_ligth:
        Change_historical("Minimo luz", lum,"Tiempo Minimo luz",timeUTC)
        historicals = get_historicals()
        Min_ligth = historicals[9]
        Time_Min_ligth = historicals[21]
        print("Min_ligth" , Min_ligth )
        print("Time_Min_ligth" , Time_Min_ligth )
     
    if rain_data < Min_rain:
        Change_historical("Minimo lluvia", rain_data, "Tiempo Minimo lluvia",timeUTC)
        historicals = get_historicals()
        Min_rain = historicals[10]
        Time_Min_rain = historicals[22]
        print("Min_rain" , Min_rain )
        print("Time_Min_rain" , Time_Min_rain )
        
    if SpeedReal_ < Min_Speed:
        Change_historical("Minimo viento", SpeedReal_,"Tiempo Minimo viento",timeUTC)
        Min_Speed = historicals[11]
        Time_Min_Speed = historicals[23]
        print("Min_Speed" , Min_Speed )
        print("Time_Min_Speed" , Time_Min_Speed )

    
        
    utime.sleep(0.5)
    
    
    
