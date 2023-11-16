#Franklin Zamora
#Ochoa Technology

from machine import I2C, UART, Pin
from SI7021 import SI7021
from mpl3115a2 import MPL3115A2
import time, machine, math
from picozero import Button

xbee = UART(1, 9600)

#I2C Start
i2c = I2C(1)
si7021 = SI7021(i2c)
i2cmpl = machine.I2C(1, scl = machine.Pin(7), sda = machine.Pin(6))


#Size Bucket rain variables and metods
BUCKET_SIZE = 0.2794
count = 0

def bucket_tipped():
    global count
    count += 1

def resetR():
    global count
    count = 0.0
    
#Wind speed variables and metods
wind_count = 0
radius_cm = 9.0
wind_interval = 1
CmInAnHour = 100000.0
SecsInAnHour = 3600
Adjustment = 1.18

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
    

while True:
    Init = b'7E 00'                                 #Bytes iniciales
    FrameType = b'10 01 '                           #Config Frame Type
    MacGW = b'00 13 A2 00 41 EA 56 17 '             #Mac Coordinador
    Options = b'FF FE 00 00 '                       #Dir 16 bits, Broadcast Radius and Options 
    frame2 = b'57 53 2F'                            #Init 'WS / '
    
    frame1 = Init
    frame2 = FrameType + MacGW + Options + frame2   #Concatenate Frame type
    
    
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
    
    wind = round(wind_dir.read_u16()* 3.3, 1)
    if wind >= 76000 and wind <= 84342:
        dir_wind = "SUR - 180/"
    elif wind >= 185000 and wind <= 190602:
        dir_wind = "OESTE - 270/"
    elif wind >= 155000 and wind <= 160000:
        dir_wind = "NORTE - 0/"
    elif wind >= 49700 and wind <= 53500:
        dir_wind = "ESTE - 90/"
    elif wind >= 71000 and wind <= 81012:
        dir_wind = "SSO - 210/"
    elif wind >= 128499 and wind <= 137000:
        dir_wind = "SUROESTE - 225/"
    elif wind >= 124000 and wind <= 133931:
        dir_wind = "SOO - 240/"
    elif wind >= 160000 and wind <= 168000:
        dir_wind = "NOO - 300/"
    elif wind >= 171500 and wind <= 176000:
        dir_wind = "NOROESTE - 315/"
    elif wind >= 138000 and wind <= 146000:
        dir_wind = "NNO - 300/"
    elif wind >= 93500 and wind <= 991000:
        dir_wind = "NNE - 30/"
    elif wind >= 101030 and wind <= 109350:
        dir_wind = "NORESTE - 45/"
    elif wind >= 46000 and wind <= 60000:
        dir_wind = "NEE - 60/"
    elif wind >= 62000 and wind <= 68500:
        dir_wind = "SURESTE - 135/"
    elif wind >= 53501 and wind <= 57000:
        dir_wind = "SSE - 150/"
    else:
        dir_wind = 'Searching'
    
    dirw_bytes = list(bytes(dir_wind, 'utf-8'))
                                                    #Speed Wind sensor Start
    
    wind_count = 0
    time.sleep(wind_interval)
    spdCstr = str(calculate_speed(wind_interval))
    speedC = spdCstr + 'Kmh/'
    speedW_bytes = list(bytes(speedC, 'utf-8'))
    
    listx = bytes(listx + temp_bytes + tempF_bytes + hum_bytes + alt_bytes + pres_bytes + lum_bytes + drop_bytes  + rain_bytes + dirw_bytes + speedW_bytes)   #Concatenate sensors
    listLn = bytes(listLn)
    
    cs = (0xFF - (sum(listx) & 0xFF))               #Checksum calculation
    cb = cs.to_bytes(1, 'big')                      #Conversion Checksum (int to byte)
    
    Lenght = len(listx)                             #Lenght calculation
    Lengthb = Lenght.to_bytes(1, 'big')             #Conversion lenght (int to byte)
    

    packet = listLn + Lengthb  + listx + cb
    print(packet)
    xbee.write(packet)
    
    
    if xbee.any() > 0:                              #Send frame demand and automatic
        dato = xbee.read(100)
        listDemand = list(dato)
        if 126 in listDemand:  #byte start '7E'
            if 14 in listDemand:  #byte lenght '00 10'
                if 144 in listDemand: #byte Frame type '10'
                    if 87 in listDemand and 83 in listDemand: #byte payload init 'WS'
                        if 112 in listDemand: #byte checksum
                            print("Demanda")
                            print(packet)
                            xbee.write(packet)
            elif 13 in listDemand:    
                if 144 in listDemand:
                    if 65 in listDemand:
                        if 217 in listDemand:
                            while True:
                                if xbee.any() > 0: #read again serial port xbee
                                    dato = xbee.read(100)
                                    listDemand = list(dato)
                                print("Automatic")
                                print(packet)
                                xbee.write(packet)
                                time.sleep(1)
                                if 7 in listDemand: 
                                    if 115 in listDemand and 116 in listDemand and 111 in listDemand and 112 in listDemand:
                                        if 84 in listDemand:
                                            print("Stop")
                                            break

    
#Main bucle


