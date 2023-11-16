from machine import I2C, UART, Pin
import time, machine, math, binascii, json
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button
from micropyGPS import MicropyGPS
from collections import OrderedDict

#Uart
xbee = UART(0, 9600)
gps = machine.UART(1, 9600)

my_gps = MicropyGPS(-7)


#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))


#Wind speed and Bucket size
wind_count = 0
radius_cm = 9.0
wind_interval = 1
CmInAnHour = 100000.0
SecsInAnHour = 3600
Adjustment = 1.18
BUCKET_SIZE = 0.2794
count = 0

#Max and min
max_temperature = -float('inf')
min_temperature = float('inf')
max_humidity = -float('inf')
min_humidity = float('inf')
max_alture = -float('inf')
min_alture = float('inf')
max_pressure = -float('inf')
min_pressure = float('inf')
max_light = -float('inf')
min_light = float('inf')
max_rain = -float('inf')
min_rain = float('inf')
max_speedw = -float('inf')
min_speedw = float('inf')

#File name json
filename = "datos.json"

#Check ND
XBeeC = False

def bucket_tipped():                             #Metod Rain 
    global count
    count += 1

def resetR():
    global count
    count = 0.0

def spin():                                      #Metod Wind Speed
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

def ND():                                        #Metod Node Discover
    
    print("Searching coordinador...")
    
    listmac = []
    global MacGW
    MacGW = b''
    global XBeeC
    
    
    frameDiscover = b'7E 00 04 08 01 4E 44 64'
    
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

def sendFrame():
    global data
    global dac
    
    with open('data.json', 'r') as file:
        # Lee el contenido del archivo
        json_content = file.read()
        
    data = json.loads(json_content)
    
    dateNOW = data['Time and date']
    tempMin = data['Temperature Min']
    tempTimeMin = data['Temperature time min']
    tempMax = data['Temperature Max']
    tempTimeMax = data['Temperature time max']
    humMin = data['Humidity Min']
    humTimeMin = data['Humidity time min']
    humMax = data['Humidity Max']
    humTimeMax = data['Humidity time max']
    alMin = data['Alture Min']
    alTimeMin = data['Alture time Min']
    alMax = data['Alture Max']
    alTimeMax = data['Alture time Max']
    presMin = data['Pressure Min']
    presTimeMin = data['Pressure time Min']
    presMax = data['Pressure Max']
    presTimeMax = data['Pressure time Max']
    rainMin = data['Rain Min']
    rainTimeMin = data['Rain time Min']
    rainMax = data['Rain Max']
    rainTimeMax = data['Rain time Max']
    speedMin = data['Speed Min']
    speedTimeMin = data['Speed time Min']
    speedMax = data['Speed Max']
    speedTimeMax = data['Speed time Max']
    
    dacRAW = str(dateNOW) + str(tempMin) + str(tempTimeMin) + str(tempMax) + str(tempTimeMax) + str(humMin)+ str(humTimeMin) + str(humMax) + str(humTimeMax)+ str(alMin) + str(alTimeMin) + str(alMax) + str(alTimeMax) + str(presMin) + str(presTimeMin) + str(presMax) + str(presTimeMax)+ str(rainMin) + str(rainTimeMin) + str(rainMax) + str(rainTimeMax) + str(speedMin) + str(speedTimeMin) + str(speedMax) + str(speedTimeMax)
    
    frame = dacRAW.replace("{", "").replace("}", "").replace(" ","").replace("'","").replace(":","")
    
    
    paquete = bytes(frame, 'utf-8')
    
    
    Init = b'7E 00'                                 #Bytes iniciales
    FrameType = b'10 01 '                           #Config Frame Type
    Options = b'FF FE 00 00 '                       #Dir 16 bits, Broadcast Radius and Options 
    frame2 = b'57 53'                               #Init 'WS / '
    frame1 = Init
    frame2 = FrameType + Options + frame2           #Concatenate Frame type
    
    listLn = []
    listx = []
    
    
    frame1 = frame1.decode('utf-8') 
    frame1 = frame1.split(' ')
    frame2 = frame2.decode('utf-8')                 #Decode frame1 and frame 2
    frame2 = frame2.split(' ')
    
    
    for y in frame1:                                #Concatenate int to array
        
        y = int(y,16)
        listLn.append(y)
    
    for x in frame2:                            
        
        x = int(x,16)
        listx.append(x)
    
    pt1 = listx[:2]
    pt2 = listx[2:]

    with open("macgw.txt", "r") as f:               #Open text file
       contenido = f.read()                         #Read text file
    macy = eval(contenido)                      
    
    listx = pt1 + list(macy) + pt2                  #Concatenate MacID after Frame ID
    
    packetList = list(paquete)
    listx = bytes(listx + packetList)
    listLn = bytes(listLn)
    
    cs = (0xFF - (sum(listx) & 0xFF))               #Checksum calculation
    cb = cs.to_bytes(1, 'big')                      #Conversion Checksum (int to byte)
    
    Lenght = len(listx)                             #Lenght calculation
    Lengthb = Lenght.to_bytes(1, 'big')             #Conversion lenght (int to byte)
    
    past = listLn + Lengthb + listx + cb
    print(past)
    xbee.write(past)
    
while True:
    
    Init = b'7E 00'                                 #Bytes iniciales
    FrameType = b'10 01 '                           #Config Frame Type
    Options = b'FF FE 00 00 '                       #Dir 16 bits, Broadcast Radius and Options 
    frame2 = b'57 53 2F'                            #Init 'WS / '
    frame1 = Init
    frame2 = FrameType + Options + frame2           #Concatenate Frame type
    
    listLn = []
    listx = []
    
    xbee.read(100)
    
    frame1 = frame1.decode('utf-8') 
    frame1 = frame1.split(' ')
    frame2 = frame2.decode('utf-8')                 #Decode frame1 and frame 2
    frame2 = frame2.split(' ')
    
    
    for y in frame1:                                #Concatenate int to array
        
        y = int(y,16)
        listLn.append(y)
    
    for x in frame2:                            
        
        x = int(x,16)
        listx.append(x)
    
    pt1 = listx[:2]
    pt2 = listx[2:]

    with open("macgw.txt", "r") as f:               #Open text file
       contenido = f.read()                         #Read text file
    macy = eval(contenido)                      
    
    listx = pt1 + list(macy) + pt2                  #Concatenate MacID after Frame ID

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
    alture = mpl.altitude()
    str_alt = str(alture)
    str_diagalt = '%RH/' + str_alt
    alt_bytes = list(bytes(str_diagalt, 'utf - 8'))
    mpl2 = MPL3115A2(i2cmpl, mode=MPL3115A2.PRESSURE)
    pressure = mpl2.pressure()
    str_pres = str(mpl2.pressure())
    str_diagpres = 'm/' + str_pres
    pres_bytes = list(bytes(str_diagpres, 'utf-8'))
    
                                                    #light sensor Start
    sensor_luz = machine.ADC(26)
    eficacia_luz = 90
    reading = sensor_luz.read_u16()
    corriente = (reading / 10000)
    lum = round(corriente * eficacia_luz, 2)
    str_lum = str(lum)
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
    speedw = calculate_speed(wind_interval)
    spdCstr = str(speedw)
    speedC = spdCstr + 'Kmh/'
    speedW_bytes = list(bytes(speedC, 'utf-8'))
    
    sensor_alt = (round(mpl.altitude()/1000, 2))
    sensor_pres = mpl2.pressure()
    
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
    
    timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
    dateNew = '{:02d}/{:02d}/{:02d}'.format(dia, mes, anio)
    
    # Obtener la hora actual
    timestamp = dateNew + " " + timeUTC
    
    
    #Concatenate all sensor (bytes) in an array
    listSens = bytes(listx + temp_bytes + tempF_bytes + hum_bytes + alt_bytes + pres_bytes + lum_bytes + drop_bytes  + rain_bytes + dirw_bytes + speedW_bytes)   #Concatenate sensors
    Astr = str(timestamp)
    listx = listSens + bytes(Astr, 'utf-8') 
    listLn = bytes(listLn)
    cs = (0xFF - (sum(listx) & 0xFF))               #Checksum calculation
    cb = cs.to_bytes(1, 'big')                      #Conversion Checksum (int to byte)
    
    Lenght = len(listx)                             #Lenght calculation
    Lengthb = Lenght.to_bytes(1, 'big')             #Conversion lenght (int to byte)
    
    packet = listLn + Lengthb + listx + cb
    
     # Actualiza los valores máximos y mínimos de temperatura
    if temperature > max_temperature:
        
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        max_temperature = temperature
        max_timeTemp = timeUTC
        
    if temperature < min_temperature:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_temperature = temperature
        min_timeTemp = timeUTC

    # Actualiza los valores máximos y mínimos de humedad
    if humidity > max_humidity:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_humidity = humidity
        max_timeHum = timeUTC

    if humidity < min_humidity:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
       
        min_humidity = humidity
        min_timehum = timeUTC
        
    if alture > max_alture:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_alture = humidity
        max_timealt = timeUTC
        
    if alture < min_alture:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_alture = humidity
        min_timealt = timeUTC
        
    if pressure > max_pressure:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_pressure = pressure
        max_timepress = timeUTC
    
    if pressure < min_pressure:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_pressure = pressure
        min_timepress = timeUTC
        
    if lum > max_light:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_light = lum
        max_timelight = timeUTC
    
    if lum < min_light:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_light = lum
        min_timelight = timeUTC
    
    if rain > max_rain:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_rain = rain
        max_timerain = timeUTC
    
    if rain < min_rain:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_rain = rain
        min_timerain = timeUTC
        
    if speedw > max_speedw:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        max_speedw = speedw
        max_timespeedw = timeUTC
    
    if speedw < min_speedw:
        #Lectura de datos GPS
        sentence = gps.readline()
        if sentence:
            for x in sentence:
                my_gps.update(chr(x))
        
        timeUTC = '{:02d}/{:02d}/{:02d}'.format(horas, minutos, segundos)
        
        min_speedw = speedw
        min_timespeedw = timeUTC
        
    # Guarda los valores máximos y mínimos con la hora en un archivo JSON
    data = OrderedDict()
    data['Time and date'] = {'/': timestamp}
    data['Temperature Min'] = {'/': min_temperature}
    data['Temperature time min'] = {'/': min_timeTemp}
    data['Temperature Max'] = {'/':max_temperature}
    data['Temperature time max'] = {'/': max_timeTemp}
    data['Humidity Min'] = {'/': min_humidity}
    data['Humidity time min'] = {'/': min_timehum}
    data['Humidity Max'] = {'/': max_humidity}
    data['Humidity time max'] = {'/': max_timeHum}
    data['Alture Min'] = {'/': min_alture}
    data['Alture time Min'] = {'/': min_timealt}
    data['Alture Max'] = {'/': max_alture}
    data['Alture time Max'] = {'/': max_timealt}
    data['Pressure Min'] = {'/': min_pressure}
    data['Pressure time Min'] = {'/': min_timepress}
    data['Pressure Max'] = {'/': max_pressure}
    data['Pressure time Max'] = {'/': max_timepress}
    data['Light Min'] = {'/': min_light}
    data['Light time Min'] = {'/': min_timelight}
    data['Light Max'] = {'/': max_light}
    data['Light time Max'] = {'/': max_timelight}
    data['Rain Min'] = {'/': min_rain}
    data['Rain time Min'] = {'/': min_timerain}
    data['Rain Max'] = {'/': max_rain}
    data['Rain time Max'] = {'/': max_timerain}
    data['Speed Min'] = {'/': min_speedw}
    data['Speed time Min'] = {'/': min_timespeedw}
    data['Speed Max'] = {'/': max_speedw}
    data['Speed time Max'] = {'/': max_timespeedw}

    with open("data.json", "w") as file:
        json.dump(data, file)
        
    sorted_data = dict(sorted(data.items()))
    
    sorted_json = json.dumps(sorted_data)

    if xbee.any() > 0:                             #Send frame demand and automatic
        dato = xbee.read(100)
        listDemand = list(dato)
        if 126 in listDemand:  #byte start '7E'
            if 14 in listDemand:  #byte lenght '14'
                if 144 in listDemand: #byte Frame type '10'
                    if 78 in listDemand and 68 in listDemand:
                        
                        ND()
                        
                    elif 87 in listDemand and 83 in listDemand: #byte 'WS'
                        print("Frame on demand sent")
                        xbee.write(packet)
                        print(type(packet))
                        print(packet)
                        
            if 14 in listDemand: #byte lenght
                if 144 in listDemand: #byte Frame type '10'
                    if 77 in listDemand and 38 in listDemand: #byte Max and Min
                        sendFrame()
                        
                        
                        
                    