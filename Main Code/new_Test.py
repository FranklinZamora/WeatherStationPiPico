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
my_gps = MicropyGPS()

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
xbee = UART(0, 9600)
gps = machine.UART(1, 115200)
my_gps = MicropyGPS()


#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))
rain_drop_sensor = machine.ADC(28)

#lenght bytes
frame = bytearray(50)

def date_hex_ascii(time_date):
    hex_ascii_digits = [ord(digito) for digito in str(time_date)]
    packed_data = ustruct.pack('BB', *hex_ascii_digits)
    return packed_data


gps_on = False
def GPS(request):
    # GPS active flag
    
    sentence = uart.readline()

    if sentence:
        # Decode GPS data
        gps_data = sentence.decode('utf-8')

        # Update the GPS object with the decoded data
        for char in gps_data:
            my_gps.update(char)

        # Extract time and date components
        horas, minutos, segundos = my_gps.timestamp
        segundos = round(segundos)
        dia, mes, ano = my_gps.date

        # Format the time and date
        timeUTC = '{:02d}:{:02d}:{:02d}'.format(horas, minutos, segundos)
        dateNew = '{:02d}-{:02d}-{:02d}'.format(dia, mes, ano)
        
        print("20" , ano)


        # Check if GPS is configured
        if ano == 80 or ano == 0:
            gps_on = False
        else:
            gps_on = True
            
        print(gps_on , "qwq")
        # Convert time and date components to bytes
        byte_hora = date_hex_ascii(horas)
        byte_minuto = date_hex_ascii(minutos)
        byte_segundo = date_hex_ascii(segundos)
        byte_dia = date_hex_ascii(dia)
        byte_mes = date_hex_ascii(mes)
        byte_ano = date_hex_ascii(ano)

        # Return values based on the request type
        if request == "Send":
            return byte_hora, byte_minuto, byte_segundo, byte_dia, byte_mes, byte_ano, timeUTC, gps_on
        
        elif request == "Status":
            return gps_on, timeUTC

    # Return default values if no GPS data is available
    return 0, 0, 0, 0, 0, 0, 0, False

#Metod Rain
def bucket_tipped():                             
    global count
    count += 1
    
def calculate_speed(time_sec):
    global wind_count
    circunferencia_cm = (2 * math.pi) * radius_cm
    rotaciones = wind_count / 2.0
    dist_km = (circunferencia_cm * rotaciones) / CmInAnHour
    kmpersec = dist_km / time_sec
    kmperhour = kmpersec * SecsInAnHour
    return kmperhour * Adjustment

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

def Data_received():
    data = ""
    data = xbee.read()
    byte_array = []
    request = False
    comand = ""
    if data:
        print("Datos recibidos:", data)
        for byte in data:
            print(hex(byte), end=' ')
            byte_array.append(byte)
        print("\nArreglo de bytes:", byte_array)
        
        if  len(byte_array) > 12 and byte_array[0] == 0x7E :
            print("lleva marca")
            request = True
            #index 1hrs - 3hrs - 5hrs
            if byte_array[15] == 0x48 and byte_array[16] == 0x02 and byte_array[17] == 0x01:
                comand = "1hr"
                print("modo 1hr activo")
            if byte_array[15] == 0x48 and byte_array[16] == 0x02 and byte_array[17] == 0x03:
                comand = "3hr"
                print("modo 3hr activo")
            if byte_array[15] == 0x48 and byte_array[16] == 0x02 and byte_array[17] == 0x05:
                comand = "5hr"
                print("modo 5hr activo")
                
    return comand
def Sensors(get_historical):
    
    global count
#     if get_historical == "True":
#         #inicializacion variables de la flash
    (Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
    Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
    Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
    Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed)  = get_historicals()
    print("iniciamos variables")
         
    
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
    rain_drop = rain_drop_sensor.read_u16()
    #print(rain_drop)

    if rain_drop >= 60001:
        count = 0
    #elif rain_drop <= 60000:
        
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
    SpeedReal_ = (int(speedReal*100))
    Speed_bytes = ustruct.pack('H', SpeedReal_)
    
    #Altura
    mpl = MPL3115A2(i2cmpl, mode=MPL3115A2.ALTITUDE) 
    alt = int((mpl.altitude() * -1) * 100) # h = (((101326 / sensor_pres) ** (1/5.257)) - 1) * 44330.8
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
    
    Gps_active,timeUTC = GPS("Status")
    utime.sleep(.2)
    
    try:
        if Gps_active == True:
            
            #Historicals Max
            if temperature > Max_temp:      
                Change_historical("Maximo temperatura", temperature,"Tiempo Maximo temperatura",timeUTC)
                Max_temp = temperature
                
            if humidity > Max_Hum:
                Change_historical("Maximo humedad" , humidity ,"Tiempo Maximo humedad", timeUTC )
                Max_Hum = humidity
                
            if pressure > Max_pressure:
                Change_historical("Maximo presion" , pressure,"Tiempo Maximo presion",timeUTC)
                Max_pressure = pressure
                       
            if lum > Max_ligth:
                Change_historical("Maximo luz", lum,"Tiempo Maximo luz",timeUTC)
                Max_ligth = lum
             
            if rain_data > Max_rain:
                Change_historical("Maximo lluvia", rain_data, "Tiempo Maximo lluvia",timeUTC)
                Max_rain = rain_data
                 
            if SpeedReal_ > Max_Speed:
                Change_historical("Maximo viento", SpeedReal_,"Tiempo Maximo viento",timeUTC)
                Max_Speed = SpeedReal_

            #Historicals MIN
            if temperature < Min_temp:
                Change_historical("Minimo temperatura" ,temperature , "Tiempo Minimo temperatura" , timeUTC )
                Min_temp = temperature
                
            if humidity < Min_Hum:
                Change_historical("Minimo humedad" , humidity ,"Tiempo Minimo humedad", timeUTC )
                Min_Hum = humidity
                
            if pressure < Min_pressure:
                Change_historical("Minimo presion" , pressure,"Tiempo Minimo presion",timeUTC)
                Min_pressure = pressure
                       
            if lum < Min_ligth:
                Change_historical("Minimo luz", lum,"Tiempo Minimo luz",timeUTC)
                Min_ligth = lum
             
            if rain_data < Min_rain:
                Change_historical("Minimo lluvia", rain_data, "Tiempo Minimo lluvia",timeUTC)
                Min_rain = rain_data
                
            if SpeedReal_ < Min_Speed:
                Change_historical("Minimo viento", SpeedReal_,"Tiempo Minimo viento",timeUTC)
                Min_Speed = SpeedReal_
    except Exception as e:
        print(f"An exception occurred: {e}")
    
    return tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes
    
def Send_Sensors_GPS():
    global count
    tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes = Sensors("Data")
    byte_hora, byte_minuto, byte_segundo , byte_dia, byte_mes, byte_ano, timeUTC, gps_  = GPS("Send")
    utime.sleep(.2)
    print("gpws ",gps_)
    
    print(byte_ano)
    if gps_ == False : #time config 0x50 = 80
        print("sin fecha")
        frame[0] = 0x7E #Start
        frame[1] = 0x00 #length
        frame[2] = 0x22
        frame[3] = 0x10 #type
        frame[4] = 0x01 #ID
        frame[5] = 0x00 #MAC
        frame[6] = 0x13
        frame[7] = 0xA2
        frame[8] = 0x00
        frame[9] = 0x41
        frame[10]= 0xEA
        frame[11]= 0x56
        frame[12]= 0x61 #END_MAC
        frame[13]= 0xFF #address
        frame[14]= 0xFE
        frame[15]= 0x00 #broadcast
        frame[16]= 0x00 #options
        frame[17] = tempCBytes[1]
        frame[18] = tempCBytes[0]
        frame[19] = tempFBytes[1]
        frame[20] = tempFBytes[0]
        frame[21] = humBytes[1]
        frame[22] = humBytes[0]          
        frame[23] = lumBytes[1]
        frame[24] = lumBytes[0]
        frame[25] = pressureBytes[3]
        frame[26] = pressureBytes[2]
        frame[27] = pressureBytes[1]
        frame[28] = pressureBytes[0]
        frame[29] = dir_wind_Bytes[1]
        frame[30] = dir_wind_Bytes[0]
        frame[31] = Speed_bytes[1]
        frame[32] = Speed_bytes[0]
        frame[33] = altBytes[1]
        frame[34] = altBytes[0]
        frame[35] = rain_bytes[1]
        frame[36] = rain_bytes[0]
        frame[37] = 0x00
        
        checksum_gps = 0xFF - (sum(frame[3:-1]) % 256)
        
        frame[37] = checksum_gps
        xbee.write(frame)
        
        for i in range(0,38):
            print(hex(frame[i]), end = ' ')
        
    else:
        print("con fecha")
        frame[0] = 0x7E #Start
        frame[1] = 0x00 #length
        frame[2] = 0x2E
        frame[3] = 0x10 #type
        frame[4] = 0x01 #ID
        frame[5] = 0x00 #MAC
        frame[6] = 0x13
        frame[7] = 0xA2
        frame[8] = 0x00
        frame[9] = 0x41
        frame[10]= 0xEA
        frame[11]= 0x56
        frame[12]= 0x61 #END_MAC
        frame[13]= 0xFF #address
        frame[14]= 0xFE
        frame[15]= 0x00 #broadcast
        frame[16]= 0x00 #options
        frame[17] = tempCBytes[1]
        frame[18] = tempCBytes[0]
        frame[19] = tempFBytes[1]
        frame[20] = tempFBytes[0]
        frame[21] = humBytes[1]
        frame[22] = humBytes[0]          
        frame[23] = lumBytes[1]
        frame[24] = lumBytes[0]
        frame[25] = pressureBytes[3]
        frame[26] = pressureBytes[2]
        frame[27] = pressureBytes[1]
        frame[28] = pressureBytes[0]
        frame[29] = dir_wind_Bytes[1]
        frame[30] = dir_wind_Bytes[0]
        frame[31] = Speed_bytes[1]
        frame[32] = Speed_bytes[0]
        frame[33] = altBytes[1]
        frame[34] = altBytes[0]
        frame[35] = rain_bytes[1]
        frame[36] = rain_bytes[0]
        frame[37] = byte_hora[0]
        frame[38] = byte_hora[1]
        frame[39] = byte_minuto[0]
        frame[40] = byte_minuto[1]
        frame[41] = byte_segundo[0]
        frame[42] = byte_segundo[1]
        frame[43] = byte_dia[0] 
        frame[44] = byte_dia[1]
        frame[45] = byte_mes[0]
        frame[46] = byte_mes[1]
        frame[47] = byte_ano[0]
        frame[48] = byte_ano[1]
        frame[49] = 0x00
        checksum = 0xFF - (sum(frame[3:-1]) % 256)
        
        frame[49] = checksum
        xbee.write(frame)

#inicializacion variables de la flash
print("Run")

#evita repetir la lectura de la flash
archivo_txt = "True" 

while True:
    data = Data_received()
    if(data == "1hr"):
        print("comando 1hr")
        Send_Sensors_GPS()
    GPS("data")
    Sensors(archivo_txt)
    archivo_txt = "False"
