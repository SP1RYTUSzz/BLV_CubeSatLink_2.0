"""
Feather and RFM95 module integration
SPI communication by Tri Do
"""
from machine import Pin, SPI 
import utime 

#Declare SPI
cs = Pin(17, Pin.OUT, value = 1)
spi = SPI(0, mosi=19, miso=16, sck = 18, baudrate=1000000)

#allocate memory
txString = "Hello from Feather\n"
rxString = ""
txData = bytearray(1)
rxData = bytearray(1)

i = 0       #index for time message repeated
while (True):
    #Keep putting in new message after txString run out
    if (txString == ""):
        txString = "repeat time " + str(i) + "\n"
        i += 1

    #SPI ENCODE: split txString into 1 byte chunk
    if (txString != ""):
        txData = bytearray(txString[0:1], "utf-8", "ignore")
        txString = txString[1:len(txString)]            #len(txString)-1 if sht happened

    #SPI EXCHANGE: conversation, 1 byte per cs cycle
    cs(0)
    spi.write_readinto(txData, rxData)
    #rxData = spi.read(1, 0xAA)
    cs(1)

    #SPI DECODE: Concaternate rxData into rxString, print & clear rxString when '\n' is detected. 
    try:
        rxString += rxData.decode("utf-8", "replace")
        if (rxData.decode("utf-8") == '\n'):
            print(rxString)
            rxString = ""
    except:
        pass
    #print(rxData)
    utime.sleep_ms(10)