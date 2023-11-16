from machine import I2C, UART, Pin
import binascii
import time
xbee = UART(1, 9600)

XBeeC = False

def ND():
    global XBeeC
    global GWMac
    GWMac = b''
    listmac = []
    
    frameDiscover = b'7E 00 04 08 01 4E 44 64'
    
    listND = []
    listx = []
    
    
    xbee.read(100)
    
    frameDiscover = frameDiscover.decode('utf-8') 
    frameDiscover = frameDiscover.split(' ')
    
    
    for y in frameDiscover:                        #Concatenate int to array
        
        y = int(y,16)
        listND.append(y)
    
    listND = bytes(listND)
    
    xbee.write(listND)
    time.sleep(15)                                 #Sed frame and wait for response
    
    
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
                    print('Coordinador!!')
                    GWMac = macID
                    print(binascii.hexlify(GWMac))
                    XbeeC = True
                    
    
        
ND()
        