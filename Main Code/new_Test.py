import utime, machine, math, binascii, os, json, micropython, gc
from machine import I2C, UART, Pin
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button
from micropyGPS import MicropyGPS
import ustruct
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
mac = bytearray(22)

def spin():                                      #Metod Wind Speed
    global wind_count
    wind_count += 1
speed = Button(9)
speed.when_activated = spin

def date_hex_ascii(time_date):
    hex_ascii_digits = [ord(digito) for digito in str(time_date)]
    packed_data = ustruct.pack('BB', *hex_ascii_digits)

    # Convertir a lista para poder modificar los valores
    packed_data = list(packed_data)

    # Ajustar los dígitos si es necesario
    for i in range(len(packed_data)):
        if packed_data[i] == 0x00:
            packed_data[i] = 0x30  # ASCII de '0'

    # Volver a empaquetar en bytes
    packed_data_s = bytes(packed_data)

    return packed_data_s

def time_hex_historicals(time_date):
    try:
        if isinstance(time_date, str):
            hora, minutos, segundos = map(int, time_date.split(':'))

            def pack_time_digit(digito):
                if 0 <= digito <= 9:
                    return ustruct.pack('B', ord(str(digito)))
                else:
                    raise ValueError("El dígito debe estar entre 0 y 9")
            
            packed_data_s = b''.join(map(pack_time_digit, divmod(segundos, 10)))
            packed_data_m = b''.join(map(pack_time_digit, divmod(minutos, 10)))
            packed_data_h = b''.join(map(pack_time_digit, divmod(hora, 10)))
            
            return packed_data_s, packed_data_m, packed_data_h
        else:
            print("time_date no es una cadena")
        
    except Exception as e:
        print(f"An exception occurred while getting bytes time: {e}")

def GPS(request):
    # GPS active flag
    gps_on = False
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
        
        print(f"20{ano}")
        print(f"{horas}:{minutos}")

        # Check if GPS is configured
        if ano == 80 or ano == 0:
            gps_on = False
        else:
            gps_on = True
            
        # Convert time and date components to bytes
        byte_segundo, byte_minuto, byte_hora = time_hex_historicals(timeUTC) #pepepepepepep
#         byte_hora = date_hex_ascii(horas)
#         byte_minuto = date_hex_ascii(minutos)
#         byte_segundo = date_hex_ascii(segundos)
        byte_dia = date_hex_ascii(dia)
        byte_mes = date_hex_ascii(mes)
        byte_ano = date_hex_ascii(ano)

        # Return values based on the request type
        if request == "Send":
            return byte_hora, byte_minuto, byte_segundo, byte_dia, byte_mes, byte_ano, timeUTC, gps_on
        
        elif request == "Status":
            #print("Status GPS")
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

def Alertas(sets):
    print(len(sets))
    temperatura_min = bytearray(2)
    temperatura_min[0] = sets[0]
    temperatura_min[1] = sets[1]
    temperatura_min_ = int.from_bytes(temperatura_min, 'big')
    
    temperatura_max = bytearray(2)
    temperatura_max[0] = sets[2]
    temperatura_max[1] = sets[3]
    temperatura_max_ = int.from_bytes(temperatura_max, 'big')
    
    humedad_min = bytearray(2)
    humedad_min[0] = sets[4]
    humedad_min[1] = sets[5]
    humedad_min_ = int.from_bytes(humedad_min, 'big')
    
    humedad_max = bytearray(2)
    humedad_max[0] = sets[6]
    humedad_max[1] = sets[7]
    humedad_max_ = int.from_bytes(humedad_max, 'big')
    
    pressure_min = bytearray(4)
    pressure_min[0] = sets[8]
    pressure_min[1] = sets[9]
    pressure_min[2] = sets[10]
    pressure_min[3] = sets[11]
    pressure_min_ = int.from_bytes(pressure_min, 'big')
    
    pressure_max = bytearray(4)
    pressure_max[0] = sets[12]
    pressure_max[1] = sets[13]
    pressure_max[2] = sets[14]
    pressure_max[3] = sets[15]
    pressure_max_ = int.from_bytes(pressure_max, 'big')
    
    speed_wind_min = bytearray(2)
    speed_wind_min[0] = sets[16]
    speed_wind_min[1] = sets[17]
    speed_wind_min_ = int.from_bytes(speed_wind_min, 'big')
    
    speed_wind_max = bytearray(2)
    speed_wind_max[0] = sets[18]
    speed_wind_max[1] = sets[19]
    speed_wind_max_ = int.from_bytes(speed_wind_max, 'big')
    
    rain_min = bytearray(2)
    rain_min[0] = sets[20]
    rain_min[1] = sets[21]
    rain_min_ = int.from_bytes(rain_min, 'big')
    
    rain_max = bytearray(2)
    rain_max[0] = sets[22]
    rain_max[1] = sets[23]
    rain_max_ = int.from_bytes(rain_max, 'big')
    
    print(f" min_temp {temperatura_min_}  max_temp {temperatura_max_} \n min_hum {humedad_min_} max_hum {humedad_max_}")
    print(f"min_pressure {pressure_min_} max_pressure {pressure_max_}\n min_speed_wind {speed_wind_min_} max_speed_wind {speed_wind_max_}")
    print(f"rain_min_ {rain_min_} rain_max_ {rain_max_}")    

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
            "Tiempo Maximo temperatura": '00:00:00',
            "Tiempo Maximo humedad": '00:00:00',
            "Tiempo Maximo presion": '00:00:00',
            "Tiempo Maximo luz": '00:00:00',
            "Tiempo Maximo lluvia": '00:00:00',
            "Tiempo Maximo viento": '00:00:00',
            "Tiempo Minimo temperatura": '00:00:00',
            "Tiempo Minimo humedad": '00:00:00',
            "Tiempo Minimo presion": '00:00:00',
            "Tiempo Minimo luz": '00:00:00',
            "Tiempo Minimo lluvia": '00:00:00',
            "Tiempo Minimo viento": '00:00:00',
            "Direccion de viento predominante": "",
            "Encendido virtual": False
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
    
    Time_Max_temp = contadores.get("Tiempo Maximo temperatura", '00:00:00')  
    Time_Max_Hum = contadores.get("Tiempo Maximo humedad", '00:00:00')
    Time_Max_pressure = contadores.get("Tiempo Maximo presion", '00:00:00')
    Time_Max_ligth = contadores.get("Tiempo Maximo luz", '00:00:00')
    Time_Max_rain = contadores.get("Tiempo Maximo lluvia", '00:00:00')
    Time_Max_Speed = contadores.get("Tiempo Maximo viento", '00:00:00')
    
    Time_Min_temp = contadores.get("Tiempo Minimo temperatura", '00:00:00')  
    Time_Min_Hum = contadores.get("Tiempo Minimo humedad", '00:00:00')
    Time_Min_pressure = contadores.get("Tiempo Minimo presion", '00:00:00')
    Time_Min_ligth = contadores.get("Tiempo Minimo luz", '00:00:00')
    Time_Min_rain = contadores.get("Tiempo Minimo lluvia", '00:00:00')
    Time_Min_Speed = contadores.get("Tiempo Minimo viento", '00:00:00')
    wind_direction = contadores.get("Direccion de viento predominante", "")
    encendido_virtual = contadores.get("Encendido virtual", False)
    
    return (
        Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
        Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
        Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
        Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed,
        wind_direction,encendido_virtual #return encendido virtual
            )
def change_dir(Sensor_name,Sensor_data):
    try:
        with open('/Max_min.txt', 'r') as file:
            historical = eval(file.read())
        
        historical[Sensor_name] = Sensor_data
        with open('/Max_min.txt', 'w') as file:
            file.write(str(historical))
            
    except (OSError, SyntaxError):
        # Si el archivo no existe o no es un diccionario válido, iniciar con un diccionario vacío
        historical = {}
    
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

def Data_received(Coordinador):
    data = ""
    data = xbee.read()
    byte_array = []
    
    if data:
        print("Datos recibidos:", data)
        for byte in data:
            print(hex(byte), end=' ')
            byte_array.append(byte)
    
        if Coordinador[1] == 0:
            if byte_array[5] == 0x4E and byte_array[6] == 0x44:#add coordinador
                print("me llego mac")
                mac = bytearray(10)
                mac[0] =  byte_array[10]
                mac[1] =  byte_array[11]
                mac[2] =  byte_array[12]
                mac[3] =  byte_array[13]
                mac[4] =  byte_array[14]
                mac[5] =  byte_array[15]
                mac[6] =  byte_array[16]
                mac[7] =  byte_array[17]
                mac[8] =  byte_array[5]
                mac[9] =  byte_array[6]
                
                mac_strings = ['{:02X}'.format(value) for value in mac]

                # Join the mac strings into a single string
                mac_string = ':'.join(mac_strings)

                # Write the mac string to a file
                with open('M_flash.txt', 'w') as file:
                    file.write(mac_string)
            
            
        if all(Coordinador[i] == byte_array[i + 4] for i in range(8)) and byte_array[15] == 0x45:
            
            if byte_array[16] == 0x54 and byte_array[17] == 0x01 and byte_array[18] == 0xB3:
                print("\nEncendido virtual")
                try:
                    with open('/Max_min.txt', 'r') as file:
                        historical = eval(file.read())
                    
                    historical["Encendido virtual"] = True
                    with open('/Max_min.txt', 'w') as file:
                        file.write(str(historical))
                        
                except (OSError, SyntaxError):
                    # Si el archivo no existe o no es un diccionario válido, iniciar con un diccionario vacío
                    historical = {}
                
            if byte_array[16] == 0x54 and byte_array[17] == 0x00 and byte_array[18] == 0xB3:
                print("\nApagado virtual")
                try:
                    with open('/Max_min.txt', 'r') as file:
                        historical = eval(file.read())
                    
                    historical["Encendido virtual"] = False
                    with open('/Max_min.txt', 'w') as file:
                        file.write(str(historical))
                        
                except (OSError, SyntaxError):
                    # Si el archivo no existe o no es un diccionario válido, iniciar con un diccionario vacío
                    historical = {}
                    
            frame_H = bytearray(120)
                    
            #format of hours message
            frame_H[0] = 0x7E #Start
            frame_H[1] = 0x00 #length
            frame_H[2] = 0x00
            frame_H[3] = 0x10 #type
            frame_H[4] = 0x01 #ID
            frame_H[5] = 0x00 #MAC
            frame_H[6] = 0x13
            frame_H[7] = 0xA2
            frame_H[8] = 0x00
            frame_H[9] = 0x41
            frame_H[10]= 0xEA
            frame_H[11]= 0x56
            frame_H[12]= 0x61 #END_MAC
            frame_H[13]= 0xFF #address
            frame_H[14]= 0xFE
            frame_H[15]= 0x00 #broadcast
            frame_H[16]= 0x00 #options
            frame_H[17] = 0x45 #header E
            frame_H[18] = 0x48 #hours comand
                
            if byte_array[16] == 0x48 and byte_array[17] == 0x02 and byte_array[18] == 0x01:
                print("\nmodo 1hr activo")
                frame_H[2] = 0x18 #adjust length
                frame_H[19] = 0x02
                frame_H[20] = 0x01
                frame_H[21] = 0x00
                checksum_gps = 0xFF - (sum(frame_H[3:-1]) % 256)
                frame_H[21] = checksum_gps
                xbee.write(frame_H)
                
                return "1hr"
            if byte_array[16] == 0x48 and byte_array[17] == 0x02 and byte_array[18] == 0x03:
                print("\ncomando 3h")
                hora = bytearray(6)
                if len(hora) == 6:
                    hora[0] =  byte_array[19]
                    hora[1] =  byte_array[20]
                    hora[2] =  byte_array[21]
                    hora[3] =  byte_array[22]
                    hora[4] =  byte_array[23]
                    hora[5] =  byte_array[24]
                    
                    frame_H[2] = 0x18 #adjust length
                    frame_H[19] = 0x02
                    frame_H[20] = 0x03
                    frame_H[21] = hora[0] 
                    frame_H[22] = hora[1] 
                    frame_H[23] = hora[2] 
                    frame_H[24] = hora[3] 
                    frame_H[25] = hora[4]
                    frame_H[26] = hora[5]
                    frame_H[27] = 0x00
                    checksum_gps = 0xFF - (sum(frame_H[3:-1]) % 256)
                    frame_H[27] = checksum_gps
                    xbee.write(frame_H)
                    
                    return hora
                    
            if byte_array[16] == 0x48 and byte_array[17] == 0x02 and byte_array[18] == 0x05:
                hora = bytearray(10)
                print("\nmodo 5hr activo")
                if len(hora) == 10:
                    hora[0] =  byte_array[19]
                    hora[1] =  byte_array[20]
                    hora[2] =  byte_array[21]
                    hora[3] =  byte_array[22]
                    hora[4] =  byte_array[23]
                    hora[5] =  byte_array[24]
                    hora[6] =  byte_array[25]
                    hora[7] =  byte_array[26]
                    hora[8] =  byte_array[27]
                    hora[9] =  byte_array[28]
                    
                    frame_H[2] = 0x1C #adjust length
                    frame_H[19] = 0x02
                    frame_H[20] = 0x03
                    frame_H[21] = hora[0] 
                    frame_H[22] = hora[1] 
                    frame_H[23] = hora[2] 
                    frame_H[24] = hora[3] 
                    frame_H[25] = hora[4]
                    frame_H[26] = hora[5]
                    frame_H[27] = hora[6] 
                    frame_H[28] = hora[7] 
                    frame_H[29] = hora[8]
                    frame_H[30] = hora[9]
                    frame_H[31] = 0x00
                    checksum_gps = 0xFF - (sum(frame_H[3:-1]) % 256)
                    frame_H[31] = checksum_gps
                    xbee.write(frame_H)
                    return hora
                
            if byte_array[16] == 0x62:
                print("bateria")
            if byte_array[16] == 0x70:
                print("panel")
#             if byte_array[16] == 0x54 and byte_array[17] == 0x01:
#                 print("on gateway")
#                 return "historicals"
            if byte_array[16] == 0x52:
                print("reset alarmas")
            if byte_array[16] == 0x73 and byte_array[17] == 0x03:
                print("send sensors")
                return "send"
            if byte_array[16] == 0x53 and byte_array[17] == 0x02:
                print("configurando setpoints")
                set_points = bytearray(24) #length message
                set_points = bytearray(byte_array[17:41])
                
                if len(set_points) == 24:
                    Alertas(set_points)
    
def search_coordinador():
    search = [20]
    #7E 00 0F 08 01 4E 44 43 6F 6F 72 64 69 6E 61 64 6F 72 F0
    search = bytes([0x7E, 0x00, 0x0F, 0x08, 0x01, 0x4E, 0x44, 0x43, 0x6F, 0x6F, 0x72, 0x64, 0x69, 0x6E, 0x61, 0x64, 0x6F, 0x72, 0xF0])
    xbee.write(search)

def send_historicals(Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed,
wind_direction,tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes):
    
    try:
        print(type(Time_Max_temp))
        frame_historicals = bytearray(120)
        
        #put condition that 1000000 equal nothing
    
        byte_Max_temp = ustruct.pack('H', Max_temp)
        Time_Max_temp_s, Time_Max_temp_m, Time_Max_temp_h = time_hex_historicals(Time_Max_temp)
        
        byte_Max_Hum = ustruct.pack('H', Max_Hum)
        Time_Max_Hum_s, Time_Max_Hum_m, Time_Max_Hum_h = time_hex_historicals(Time_Max_Hum)
        
        byte_Max_pressure = ustruct.pack('I', Max_pressure)
        Time_Max_pressure_s, Time_Max_pressure_m, Time_Max_pressure_h = time_hex_historicals(Time_Max_pressure)
        
        byte_Max_ligth = ustruct.pack('H', Max_ligth)
        Time_Max_ligth_s, Time_Max_ligth_m, Time_Max_ligth_h = time_hex_historicals(Time_Max_ligth)
        
        byte_Max_rain = ustruct.pack('H', Max_rain)
        Time_Max_rain_s, Time_Max_rain_m, Time_Max_rain_h = time_hex_historicals(Time_Max_rain)
        
        byte_Max_Speed = ustruct.pack('H', Max_Speed)
        Time_Max_Speed_s, Time_Max_Speed_m, Time_Max_Speed_h = time_hex_historicals(Time_Max_Speed)
        
        byte_Min_temp = ustruct.pack('H',Min_temp)
        Time_Min_temp_s, Time_Min_temp_m, Time_Min_temp_h = time_hex_historicals(Time_Min_temp)
        
        byte_Min_Hum = ustruct.pack('H',Min_Hum)
        Time_Min_Hum_s, Time_Min_Hum_m, Time_Min_Hum_h = time_hex_historicals(Time_Min_Hum)
        
        byte_Min_pressure = ustruct.pack('I', Min_pressure)
        Time_Min_pressure_s, Time_Min_pressure_m, Time_Min_pressure_h = time_hex_historicals(Time_Min_pressure)
        
        byte_Min_ligth = ustruct.pack('H', Min_ligth)
        Time_Min_ligth_s, Time_Min_ligth_m, Time_Min_ligth_h = time_hex_historicals(Time_Min_ligth)
        
        byte_Min_rain = ustruct.pack('H', Min_rain)
        Time_Min_rain_s, Time_Min_rain_m, Time_Min_rain_h = time_hex_historicals(Time_Min_rain)
        
        byte_Min_Speed = ustruct.pack('H', Min_Speed)
        Time_Min_Speed_s, Time_Min_Speed_m, Time_Min_Speed_h = time_hex_historicals(Time_Min_Speed)
        
        frame_historicals[0] = 0x7E #Start
        frame_historicals[1] = 0x00 #length
        frame_historicals[2] = 0x71
        frame_historicals[3] = 0x10 #type
        frame_historicals[4] = 0x01 #ID
        frame_historicals[5] = 0x00 #MAC
        frame_historicals[6] = 0x13
        frame_historicals[7] = 0xA2
        frame_historicals[8] = 0x00
        frame_historicals[9] = 0x41
        frame_historicals[10]= 0xEA
        frame_historicals[11]= 0x56
        frame_historicals[12]= 0x61 #END_MAC
        frame_historicals[13]= 0xFF #address
        frame_historicals[14]= 0xFE
        frame_historicals[15]= 0x00 #broadcast
        frame_historicals[16]= 0x00 #options
        frame_historicals[17] = 0x45 #header E
        
        frame_historicals[18] = tempCBytes[1]
        frame_historicals[19] = tempCBytes[0]
        frame_historicals[20] = byte_Min_temp[1]
        frame_historicals[21] = byte_Min_temp[0]
        frame_historicals[22] = Time_Min_temp_h[0]
        frame_historicals[23] = Time_Min_temp_h[1]
        frame_historicals[24] = Time_Min_temp_m[0]
        frame_historicals[25] = Time_Min_temp_m[1]
        frame_historicals[26] = byte_Max_temp[1]
        frame_historicals[27] = byte_Max_temp[0]
        frame_historicals[28] = Time_Max_temp_h[0]
        frame_historicals[29] = Time_Max_temp_h[1]
        frame_historicals[30] = Time_Max_temp_m[0]
        frame_historicals[31] = Time_Max_temp_m[1]
        
        frame_historicals[32] = humBytes[1]
        frame_historicals[33] = humBytes[0]
        frame_historicals[34] = byte_Min_Hum[1]
        frame_historicals[35] = byte_Min_Hum[0]
        frame_historicals[36] = Time_Min_Hum_h[0]
        frame_historicals[37] = Time_Min_Hum_h[1]
        frame_historicals[38] = Time_Min_Hum_m[0]
        frame_historicals[39] = Time_Min_Hum_m[1]
        frame_historicals[40] = byte_Max_Hum[1]
        frame_historicals[41] = byte_Max_Hum[0]
        frame_historicals[42] = Time_Max_Hum_h[0]
        frame_historicals[43] = Time_Max_Hum_h[1]
        frame_historicals[44] = Time_Max_Hum_m[0]
        frame_historicals[45] = Time_Max_Hum_m[1]
        
        frame_historicals[46] = lumBytes[1]
        frame_historicals[47] = lumBytes[0]
        frame_historicals[48] = byte_Min_ligth[1]
        frame_historicals[49] = byte_Min_ligth[0]
        frame_historicals[50] = Time_Min_ligth_h[0]
        frame_historicals[51] = Time_Min_ligth_h[1]
        frame_historicals[52] = Time_Min_ligth_m[0]
        frame_historicals[53] = Time_Min_ligth_m[1]
        frame_historicals[54] = byte_Max_ligth[1]
        frame_historicals[55] = byte_Max_ligth[0]
        frame_historicals[56] = Time_Max_ligth_h[0]
        frame_historicals[57] = Time_Max_ligth_h[1]
        frame_historicals[58] = Time_Max_ligth_m[0]
        frame_historicals[59] = Time_Max_ligth_m[1]
        
        frame_historicals[60] = pressureBytes[3]
        frame_historicals[61] = pressureBytes[2]
        frame_historicals[62] = pressureBytes[1]
        frame_historicals[63] = pressureBytes[0]
        frame_historicals[64] = byte_Min_pressure[3]
        frame_historicals[65] = byte_Min_pressure[2]
        frame_historicals[66] = byte_Min_pressure[1]
        frame_historicals[67] = byte_Min_pressure[0]
        frame_historicals[68] = Time_Min_pressure_h[0]
        frame_historicals[69] = Time_Min_pressure_h[1]
        frame_historicals[70] = Time_Min_pressure_m[0]
        frame_historicals[71] = Time_Min_pressure_m[1]
        frame_historicals[72] = byte_Max_pressure[1]
        frame_historicals[73] = byte_Max_pressure[0]
        frame_historicals[74] = Time_Max_pressure_h[0]
        frame_historicals[75] = Time_Max_pressure_h[1]
        frame_historicals[76] = Time_Max_pressure_m[0]
        frame_historicals[77] = Time_Max_pressure_m[1]
        
        frame_historicals[78] = Speed_bytes[1]
        frame_historicals[79] = Speed_bytes[0]
        frame_historicals[80] = byte_Min_Speed[1]
        frame_historicals[81] = byte_Min_Speed[0]
        frame_historicals[82] = Time_Min_Speed_h[0]
        frame_historicals[83] = Time_Min_Speed_h[1]
        frame_historicals[84] = Time_Min_Speed_m[0]
        frame_historicals[85] = Time_Min_Speed_m[1]
        frame_historicals[86] = byte_Max_Speed[1]
        frame_historicals[87] = byte_Max_Speed[0]
        frame_historicals[88] = Time_Max_Speed_h[0]
        frame_historicals[89] = Time_Max_Speed_h[1]
        frame_historicals[90] = Time_Max_Speed_m[0]
        frame_historicals[91] = Time_Max_Speed_m[1]
        
        frame_historicals[92] = rain_bytes[1]
        frame_historicals[93] = rain_bytes[0]
        frame_historicals[94] = byte_Max_rain[1]
        frame_historicals[95] = byte_Max_rain[0]
        frame_historicals[96] = Time_Max_rain_h[0]
        frame_historicals[97] = Time_Max_rain_h[1]
        frame_historicals[98] = Time_Max_rain_m[0]
        frame_historicals[99] = Time_Max_rain_m[1]
        frame_historicals[100] = byte_Min_rain[1]
        frame_historicals[101] = byte_Min_rain[0]
        frame_historicals[102] = Time_Min_rain_h[0]
        frame_historicals[103] = Time_Min_rain_h[1]
        frame_historicals[104] = Time_Min_rain_m[0]
        frame_historicals[105] = Time_Min_rain_m[1]
        
        
        frame_historicals[106] = altBytes[1]
        frame_historicals[107] = altBytes[0]
        frame_historicals[108] = dir_wind_Bytes[1]
        frame_historicals[109] = dir_wind_Bytes[0]
        #put dir_predominant
        
        frame_historicals[110] = 0x00
        checksum_gps = 0xFF - (sum(frame_historicals[3:-1]) % 256)
        frame_historicals[110] = checksum_gps
        xbee.write(frame_historicals)
        
        for i in range(0,111):
            print(hex(frame_historicals[i]), end = ' ')
        
    except Exception as e:
        print(f"An exception occurred while get bytes date: {e}")

def Send_Sensors_GPS(tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes):
    
    frame[0] = 0x7E #Start
    frame[1] = 0x00 #length
    frame[2] = 0x23
    frame[3] = 0x10 #type
    frame[4] = 0x00 #ID
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
    frame[17]= 0x45 #header
    frame[18] = tempCBytes[1]
    frame[19] = tempCBytes[0]
    frame[20] = tempFBytes[1]
    frame[21] = tempFBytes[0]
    frame[22] = humBytes[1]
    frame[23] = humBytes[0]          
    frame[24] = lumBytes[1]
    frame[25] = lumBytes[0]
    frame[26] = pressureBytes[3]
    frame[27] = pressureBytes[2]
    frame[28] = pressureBytes[1]
    frame[29] = pressureBytes[0]
    frame[30] = dir_wind_Bytes[1]
    frame[31] = dir_wind_Bytes[0]
    frame[32] = Speed_bytes[1]
    frame[33] = Speed_bytes[0]
    frame[34] = altBytes[1]
    frame[35] = altBytes[0]
    frame[36] = rain_bytes[1]
    frame[37] = rain_bytes[0]
    frame[38] = 0x00
    checksum_gps = 0xFF - (sum(frame[3:-1]) % 256)
    frame[38] = checksum_gps
    xbee.write(frame)
    
    for i in range(0,39):
        print(hex(frame[i]), end = ' ')
        
def obtener_direccion_viento_actual(wind, wind_directions):
    for direction, lower, upper in wind_directions:
        if lower <= wind <= upper:
            return direction
    return None

def obtener_direccion_viento_predominante(wind_directions):
    direction_freq = {}
    
    for direction, _, _ in wind_directions:
        if direction in direction_freq:
            direction_freq[direction] += 1
        else:
            direction_freq[direction] = 1
    
    predominant_direction = max(direction_freq, key=direction_freq.get)
    return predominant_direction
        
def get_mac():
    try:
        with open('M_flash.txt', 'r') as file:
            mac_string = file.read().strip()
            print(mac_string)
            if mac_string != "":
                mac_parts = mac_string.split(":") 
                mac_bytes = bytes([int(part, 16) for part in mac_parts]) # Convierte cada parte a un valor entero y luego a bytes
                print(mac_bytes[0:9])
                return mac_bytes
            else:
                print("empty")
                return [0x00,0x00]
    except Exception as e:
        print(f"An exception occurred while getting MAC: {e}")
        return b""

#inicializacion variables de la flash
print("Run")
    
(Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed,
wind_direction,encendido_virtual)  = get_historicals() #si 

#predominant wind
predominant_directions_count = {
    "NORTE": 0,
    "ESTE": 0,
    "SUR": 0,
    "OESTE": 0,
    "NE": 0,
    "NNE": 0,
    "ESE": 0,
    "SE": 0,
    "SSE": 0,
    "SSO": 0,
    "SO": 0,
    "OSO": 0,
    "ONO": 0,
    "NO": 0,
    }

#search_coordinador()
Coordinador = bytearray(10)
consular_mac = False
Coordinador = get_mac()
print("this ",Coordinador)

last_time = 0
hora_1=0
hora_2=0
hora_3=0
hora_1_bool = False
hora_2_bool = False
hora_3_bool = False

hora_4 = 0
hora_5 = 0
hora_4_bool = False
hora_5_bool = False

comando_1h = False
comando_3hrs = False
comando_5hrs = False
ascii_minute = 0

last_wind_directions = ""

contador_mac = 15

while True:
    try: 
        data = ""  
        if Coordinador[1] != 0: #check flash if there's data
            if Coordinador[8] == 0x4E and Coordinador[9] == 0x44: #check txt ND
                contador_mac = 0
                pass
                #print("se tiene coordinador ")
        else:
            if contador_mac >= 16:
                contador_mac = 0
            print("llegando a 15 para enviar ",contador_mac)
            if contador_mac == 15:
                print("buscar coordinador")
                search_coordinador()
                consular_mac = True
            contador_mac+=1
                
        data = Data_received(Coordinador)  
        if consular_mac == True:
            Coordinador = get_mac()
            consular_mac = False
           
        byte_hora, byte_minuto, byte_segundo, byte_dia, byte_mes, byte_ano, timeUTC, Gps_active = GPS("Send")
        
        print(data)
        
        if isinstance(data,bytearray) and len(data) == 6: #check data list of bytes 3hrs
            print("tiene las horas", data)
            comando_1h = False
            comando_3hrs = True
            comando_5hrs = False
            hora_1_bool = True
            hora_2_bool = True
            hora_3_bool = True
            hora1 = data[0:2]
            hora_1  = int(hora1.decode('ascii'))
            hora2 = data[2:4]
            hora_2  = int(hora2.decode('ascii'))
            hora3 = data[4:6]
            hora_3  = int(hora3.decode('ascii'))
            
        if isinstance(data,bytearray) and len(data) == 10: #check data list of bytes 10hrs
            comando_5hrs = True
            comando_3hrs = False
            comando_1h = False
            hora_1_bool = True
            hora_2_bool = True
            hora_3_bool = True
            hora_4_bool = True
            hora_5_bool = True
            hora1 = data[0:2]
            hora_1  = int(hora1.decode('ascii'))
            hora2 = data[2:4]
            hora_2  = int(hora2.decode('ascii'))
            hora3 = data[4:6]
            hora_3  = int(hora3.decode('ascii'))
            hora4 = data[6:8]
            hora_4  = int(hora4.decode('ascii'))
            hora5 = data[8:10]
            hora_5  = int(hora5.decode('ascii'))
        
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
        if rain_drop >= 60001:
            count = 0
            
        #rain sensor
        rain_sensor = Button(8)
        rain_sensor.when_pressed = bucket_tipped
        rain = count * BUCKET_SIZE
        str_rain = str(rain)
        str_pRain = str_rain + 'mm/'
        rain_data = (int(rain*100))
        rain_bytes = ustruct.pack('H', rain_data)
            
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
        
        #request data  to GPS
        byte_hora, byte_minuto, byte_segundo, byte_dia, byte_mes, byte_ano, timeUTC, Gps_active = GPS("Send")
        utime.sleep(.5)
        
        enviar = False #control de envio
        
        if data == "send":
            if Gps_active == False : #time config 0x50 = 80
                Send_Sensors_GPS(tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes)
            #send data
            if Gps_active == True:
                enviar = True
                print("enviando historicos")
        
        if Gps_active == True:
            try:
                ascii_minute = int(''.join(filter(str.isdigit, byte_minuto.decode('ascii'))))
            except ValueError as e:
                print("Error converting byte_minuto to integer:", e)
                
            current_time =  ascii_minute 
            if data == "1hr":
                comando_1h = True
                comando_3hrs = False
                comando_5hrs = False
                last_time =  ascii_minute - 1
                
            if current_time == 0: #change 23 -> 00
                last_time = 0
                
            if comando_1h == True:
                print("now ",current_time)
                print("last",last_time)
                print(current_time - last_time)
                if current_time - last_time == 1:
                    enviar = True
                    last_time = current_time
                    print("send every hour")
                    
            if comando_3hrs == True:
                if ascii_minute == hora_1 and hora_1_bool == True:
                    enviar = True
                    hora_1_bool = False
                if ascii_minute == hora_2 and hora_2_bool == True:
                    enviar = True
                    hora_2_bool = False
                if ascii_minute == hora_3 and hora_3_bool == True:
                    enviar = True
                    hora_3_bool = False
                    
            if comando_5hrs == True:
                if ascii_minute == hora_1 and hora_1_bool == True:
                    enviar = True
                    hora_1_bool = False
                if ascii_minute == hora_2 and hora_2_bool == True:
                    enviar = True
                    hora_2_bool = False
                if ascii_minute == hora_3 and hora_3_bool == True:
                    enviar = True
                    hora_3_bool = False
                if ascii_minute == hora_4 and hora_4_bool == True:
                    enviar = True
                    hora_4_bool = False
                if ascii_minute == hora_5 and hora_5_bool == True:
                    enviar = True
                    hora_5_bool = False
            if enviar  == True:
                send_historicals(Max_temp, Max_Hum, Max_pressure, Max_ligth, Max_rain, Max_Speed,
                Min_temp, Min_Hum, Min_pressure, Min_ligth, Min_rain, Min_Speed,
                Time_Max_temp,Time_Max_Hum,Time_Max_pressure,Time_Max_ligth,Time_Max_rain,Time_Max_Speed,
                Time_Min_temp,Time_Min_Hum,Time_Min_pressure,Time_Min_ligth,Time_Min_rain,Time_Min_Speed,
                wind_direction,tempCBytes, tempFBytes, humBytes, lumBytes, pressureBytes, dir_wind_Bytes, Speed_bytes, altBytes, rain_bytes)                 
        
        #calculate historical wind direction
        predominant_directions_count[dir_wind] += 1
        most_common_direction = max(predominant_directions_count, key=predominant_directions_count.get)
        #print("Dirección del viento más frecuente:", most_common_direction)
        highest_value = predominant_directions_count[most_common_direction]
        
        #restart direction
        if ascii_minute == 00:
            predominant_directions_count = {
            "NORTE": 0,
            "ESTE": 0,
            "SUR": 0,
            "OESTE": 0,
            "NE": 0,
            "NNE": 0,
            "ESE": 0,
            "SE": 0,
            "SSE": 0,
            "SSO": 0,
            "SO": 0,
            "OSO": 0,
            "ONO": 0,
            "NO": 0,
            }
        try: #encendido virtual
            if Gps_active == True:
                if encendido_virtual == True:
                    
                    if most_common_direction != last_wind_directions:
                        last_wind_directions = most_common_direction
                        print("guardando")
                        try:
                            with open('/Max_min.txt', 'r') as file:
                                historical = eval(file.read())
                            
                            historical["Direccion de viento predominante"] = dir_wind
                            with open('/Max_min.txt', 'w') as file:
                                file.write(str(historical))
                                
                        except (OSError, SyntaxError):
                            # Si el archivo no existe o no es un diccionario válido, iniciar con un diccionario vacío
                            historical = {}
                    
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
            print(f"An exception occurred historicals: {e}")             
    except Exception as e:
                print(f"An exception occurred in general code: {e}")
        

