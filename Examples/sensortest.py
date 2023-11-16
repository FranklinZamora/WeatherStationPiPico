import time, machine, math, binascii, os, json, micropython, gc
from machine import I2C, UART, Pin
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button
from micropyGPS import MicropyGPS


#XBee
xbee = UART(0, 9600)

#Inicio GPS
gps = machine.UART(1, 9600)
my_gps = MicropyGPS(-7)

#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))

# Nombre del archivo de texto donde se guardarán los valores del sensor
filename = "datos.json"

#Wind speed and Bucket size
wind_count = 0
radius_cm = 9.0
wind_interval = 1
CmInAnHour = 100000.0
SecsInAnHour = 3600
Adjustment = 1.18
BUCKET_SIZE = 0.2794
count = 0

#Eraser content
def eraser():
    with open(filename, "w") as f:
        pass

#Get local time
def get_current_time():
    current_time = utime.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(current_time[0], current_time[1], current_time[2], current_time[3], current_time[4], current_time[5])

#Max & min read
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

#Rain tick
def bucket_tipped():                              
    global count
    count += 1

#Reset Rain
def resetR():
    global count
    count = 0.0

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

#Metod Node Discover
def ND():                                        
    
    print("Searching coordinador...")
    
    listmac = []
    global MacGW
    MacGW = b''
    global XBeeC
    
    
    frameDiscover = b'7E 00 10 10 01 00 13 A2 00 41 B1 85 34 FF FE 00 00 4E 44 FF'
    
    listND = []
    listx = []
    
    
    #xbee.read(100)
    
    frameDiscover = frameDiscover.decode('utf-8') 
    frameDiscover = frameDiscover.split(' ')
    
    
    for y in frameDiscover:                        #Concatenate int to array
        
        y = int(y,16)
        listND.append(y)
    
    listND = bytes(listND)
    
    xbee.write(listND)
                                     #Sed frame and wait for response
    
    time.sleep(15)
    while True:
        if xbee.any() > 0:                         #Check bus
            count = 0

            xbresp = xbee.read(3)
            strResp = binascii.hexlify(xbresp)
            lit = strResp[4:6]
            p1 = int(lit, 16)
            p1 = p1 + 1
            x = xbee.read(p1)
            
            if x[0] == 0x88:
                macID = x[7:15]
                
                for i in x[15:47]:
                    count+=1
                    
                    if i == 0:
                        break
                
                NIFinal = 14 + count
                NI = (x[15:NIFinal])
                
                if b'Coordinador' in NI:
                    print('Coordinador found')
                    print('MacID: ' + str(macID))
                    print("Ready ✓")
                    
                    MacGW = macID
                    text = open("macgw.txt", "w")
                    text.write(str(MacGW))
                    text.close()
                    XBeeC = True
                    
                time.sleep(0.1)
            else:
                pass
        else:
            break

while True:
    if XBeeC == False:
        ND()
    if XBeeC == True:

        Init = b'7E 00'                                 #Bytes iniciales
        FrameType = b'10 01 '                           #Config Frame Type
        Options = b'FF FE 00 00 '                       #Dir 16 bits, Broadcast Radius and Options 
        frame2 = b'57 53 2F'                            #Init 'WS / '
        frame1 = Init
        frame2 = FrameType + Options + frame2           #Concatenate Frame type
        global listSt
        listSt = []
        global listx
        listx = []
        
        xbee.read(100)
        
        #Decode frame1 and frame 2
        frame1 = frame1.decode('utf-8') 
        frame1 = frame1.split(' ')
        frame2 = frame2.decode('utf-8')                 
        frame2 = frame2.split(' ')
        
        #Concatenate int to array
        for y in frame1:                                
            
            y = int(y,16)
            listSt.append(y)
        
        for x in frame2:                            
            
            x = int(x,16)
            listx.append(x)
        
        pt1 = listx[:2]
        pt2 = listx[2:]
        #Concatenate MacID after Frame ID
        listx = pt1 + pt2                             

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
        
        #Temperature and Humedity sensor Start
        temperature = (round(si7021.temperature(), 2))
        str_temp = str(temperature)
        temp_bytes = list(bytes(str_temp, 'utf-8'))
        temperatureF = (round(si7021.temperature() * 9/5 + 32, 2))
        str_tempF = str(temperatureF)
        str_diagtempF = 'C/' + str_tempF
        tempF_bytes = list(bytes(str_diagtempF, 'utf-8'))                                                 
        humidity = (round(si7021.humidity(), 2))
        str_hum = str(humidity)
        str_diaghum = 'F/' + str_hum
        hum_bytes = list(bytes(str_diaghum, 'utf-8'))
        
                                                        #Altimeter and Pressure sensor Start
        mpl = MPL3115A2(i2cmpl, mode=MPL3115A2.ALTITUDE) 
        str_alt = str(mpl.altitude() * -1)
        str_diagalt = '%RH/' + str_alt
        alt_bytes = list(bytes(str_diagalt, 'utf - 8'))
        mpl2 = MPL3115A2(i2cmpl, mode=MPL3115A2.PRESSURE)
        str_pres = str(mpl2.pressure())
        str_diagpres = 'm/' + str_pres
        pres_bytes = list(bytes(str_diagpres, 'utf-8'))
        
                                                        #light sensor Start
        sensor_luz = machine.ADC(26)
        eficacia_luz = 90
        reading = sensor_luz.read_u16()
        corriente = (reading / 10000)
        str_lum = str(round(corriente * eficacia_luz, 2))
        str_diaglum = 'Pa/' + str_lum + 'Lm/'
        lum_bytes = list(bytes(str_diaglum, 'utf-8'))
                                                        #Rain Drop sensor Start
        raindrop = machine.ADC(28)
        rain_status = ''
        rain_drop = raindrop.read_u16()
        if rain_drop >= 51000:
            rainIf = 'False/'
            count = 0.0
                
        elif rain_drop <= 50000:
            rainIf = 'True/'
        drop_bytes = list(bytes(rainIf, 'utf-8'))
                                                        #Rain sensor Start
        
        rain_sensor = Button(8)
        rain_sensor.when_pressed = bucket_tipped
        
        rain = count * BUCKET_SIZE
        rain_drop = raindrop.read_u16()
        
        str_rain = str(rain)
        str_pRain = str_rain + 'mm/'
        rain_bytes = list(bytes(str_pRain, 'utf-8'))
                                                        #Dir Wind sensor Start
        wind_dir = machine.ADC(27)
        dir_wind = ""
        
        wind = round((wind_dir.read_u16() * 3.3) / 1000, 1)
        
        if wind >= 189.2 and wind <= 194.8:
            dir_wind = "NORTE/"
        if wind >= 83.4 and wind <= 86.91:
            dir_wind = "ESTE/"
        if wind >= 119.8 and wind <= 126.2:
            dir_wind = "SUR/"
        if wind >= 205.5 and wind <= 210.9:
            dir_wind = "OESTE/"
        if wind >= 147.7 and wind <= 151.4:
            dir_wind = "NE/"
        if wind >= 136.3 and wind <= 143.5:
            dir_wind = "NNE/"
        if wind >= 78.2 and wind <= 85.2:
            dir_wind = "ESE/"
        if wind >= 101.1 and wind <= 109.0:
            dir_wind = "SE/"
        if wind >= 90.5 and wind <= 96.2:
            dir_wind = "SSE/"
        if wind >= 112.5 and wind <= 116.8:
            dir_wind = "SSO/"
        if wind >= 170.3 and wind <= 177.8:
            dir_wind = "SO/"
        if wind >= 167.0 and wind <= 169.6:
            dir_wind = "OSO/"
        if wind >= 167.0 and wind <= 169.6:
            dir_wind = "OSO/"
        if wind >= 194.5 and wind <= 197.1:
            dir_wind = "ONO/"
        if wind >= 201.6 and wind <= 205.4:
            dir_wind = "NO/"
        if wind >= 180.7 and wind <= 201.3:
            dir_wind = "NO/"
        
        dirw_bytes = list(bytes(dir_wind, 'utf-8'))
                                                        #Speed Wind sensor Start
        
        wind_count = 0
        time.sleep(wind_interval)
        spdCstr = str(calculate_speed(wind_interval))
        speedC = spdCstr + 'Kmh/'
        speedW_bytes = list(bytes(speedC, 'utf-8'))

        #Valor Sensores CHANGE NAMES 
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
            
        micropython.alloc_emergency_exception_buf(100)
        
        gc.collect()

        leer_maxmin()
            
        print("--------------------------------------------------------------------------------------------------")

        
        listx = bytes(listx + temp_bytes + tempF_bytes + hum_bytes + alt_bytes + pres_bytes + lum_bytes + drop_bytes  + rain_bytes + dirw_bytes + speedW_bytes)   #Concatenate sensors
        listSt = bytes(listSt)

        cs = (0xFF - (sum(listx) & 0xFF))               #Checksum calculation
        cb = cs.to_bytes(1, 'big')                      #Conversion Checksum (int to byte)
        
        Lenght = len(listx)                             #Lenght calculation
        Lengthb = Lenght.to_bytes(1, 'big')             #Conversion lenght (int to byte)
        
        packet = listSt + Lengthb + listx + cb

        print(packet)

        time.sleep(1)
    

