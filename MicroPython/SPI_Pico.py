from machine import Pin, SPI 
import utime 

#Declare SPI
cs = Pin(17, Pin.OUT, value = 1)
spi = SPI(0, mosi=19, miso=16, sck = 18, baudrate=1000000)

UnicodeErrorOccurence = 0

#allocate memory
txString0 = "This is UART0 channel\n"
txString1 = "Speaking to UART1\n"
rxString0 = ""
rxString1 = ""
txData0 = bytearray(1)
rxData0 = bytearray(1)
txData1 = bytearray(1)
rxData1 = bytearray(1)
selection = bytearray(1)    #see which UART Pico is receiving and relaying from 

i0 = 0       #index for time message repeated
i1 = 0
while (True):
    try:
        #Keep putting in new message after txString run out
        if (txString0 == ""):
            txString0 = "uart0 repeat time " + str(i0) + "\n"
            i0 += 1
        if (txString1 == ""):
            txString1 = "uart1 repeating time " + str(i1) + "\n"
            i1 += 1
        
        #SPI ENCODE: split txString into 1 byte chunk
        if (txString0 != ""):
            txData0 = bytearray(txString0[0:1], "utf-8", "ignore")
            txString0 = txString0[1:len(txString0)]            #len(txString)-1 if sht happened
        if (txString1 != ""):
            txData1 = bytearray(txString1[0:1], "utf-8", "ignore")
            txString1 = txString1[1:len(txString1)]            #len(txString)-1 if sht happened

        #SPI EXCHANGE: conversation, 1 byte per cs cycle
        cs(0)
        spi.write_readinto('#', selection)
        cs(1)
        if (selection == '`'):
            cs(0)
            spi.write_readinto(txData0, rxData0)
            cs(1)
            cs(0)
            spi.write_readinto(txData1, rxData1)
            cs(1)
            rxString0 += rxData0.decode('utf-8', 'ignore')
            if (rxData0.decode('utf-8', 'ignore') == '\n'):
                print("Message from UART0: ", rxString0)
                rxString0 = ""
            rxString1 += rxData1.decode('utf-8', 'ignore')
            if (rxData1.decode('utf-8', 'ignore') == '\n'):
                print("Message from UART1: ", rxString1)
                rxString1 = ""
        """
        if (rxData1 != '\x00'):
            print(rxData0, rxData1)
        if (rxData0 != '\x00'):
            print(rxData0, rxData1)
        """
        utime.sleep_us(100)
    except UnicodeError:
        print("Unicode Error time ", UnicodeErrorOccurence)
        UnicodeErrorOccurence += 1
