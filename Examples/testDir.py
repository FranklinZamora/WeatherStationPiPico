import time, machine, math, binascii, os
from machine import I2C, UART, Pin
from mpl3115a2 import MPL3115A2
from SI7021 import SI7021
from picozero import Button

#Uart
xbee = UART(1, 9600)

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

while True:
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
    
    frame1 = frame1.decode('utf-8') 
    frame1 = frame1.split(' ')
    frame2 = frame2.decode('utf-8')                 #Decode frame1 and frame 2
    frame2 = frame2.split(' ')
    
    
    for y in frame1:                                #Concatenate int to array
        
        y = int(y,16)
        listSt.append(y)
    
    for x in frame2:                            
        
        x = int(x,16)
        listx.append(x)
    
    pt1 = listx[:2]
    pt2 = listx[2:]
    listx = pt1 + pt2               #Concatenate MacID after Frame ID

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
    str_alt = str(mpl.altitude() * 10)
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
    
    listx = bytes(listx + temp_bytes + tempF_bytes + hum_bytes + alt_bytes + pres_bytes + lum_bytes + drop_bytes  + rain_bytes + dirw_bytes + speedW_bytes)   #Concatenate sensors
    listSt = bytes(listSt)
    print(listx)

    time.sleep(1)
    




