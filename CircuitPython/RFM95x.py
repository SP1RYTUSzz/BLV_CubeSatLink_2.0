import board
import busio
import digitalio
from adafruit_datetime import datetime
import time
import adafruit_rfm9x
import os    # To utilize file operations

from board import *
from adafruit_bus_device.spi_device import SPIDevice



# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
#These are for RFM9x, not SPI
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D6)


# Define the onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

#init SPI
with busio.SPI(SCK, MOSI, MISO) as spi_bus:
    cs = digitalio.DigitalInOut(D257)
    device = SPIDevice(spi_bus, cs)
# Initialize SPI bus.y
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Note that the radio is configured in LoRa mode so you can't control sync
# word, encryption, frequency deviation, or other settings!

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23

# Send a packet.  Note you can only send a packet up to 252 bytes in length.
# This is a limitation of the radio packet size, so if you need to send larger
# amounts of data you will need to break it into smaller send calls.  Each send
# call will wait for the previous one to finish before continuing.
rx_raw_string = ""
state = 0

#Starting Tri's code
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

while True:
    """
    packet2 = (rfm9x.send(input(bytes("Enter passkey...", "utf-8"))))
    
    # File Operation sending:
    with open('TEST_INTRO.txt', 'r') as f:
        fileToSend = f.read()
        packet3 = (rfm9x.send(bytes(fileToSend, "utf-8")))
    print("Sent message 1.")
    time.sleep(2)
    output_time = datetime.now()
    print("Message sent at:", output_time)
    """
    
    while not spi.try_lock():
        pass
    try:
        spi.configure(baudrate=1000000)
        cs.value = False
        cs.value = True
    finally:
        spi.unlock()

    #Starting Tri's Code
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
    while not spi.try_lock():
        pass
    try:
        spi.configure(baudrate=1000000)
        cs.value = False
        spi.write_readinto('#', selection)
        cs.value = True
    finally:
        spi.unlock()

    if (selection == '`'):
        while not spi.try_lock():
            pass
        try:
            spi.configure(baudrate=1000000)
            cs.value = False
            spi.write_readinto(txData0, rxData0)
            cs.value = True
            cs.value = False
            spi.write_readinto(txData1, rxData1)
            cs.value = True
        finally:
            spi.unlock()
            
        rxString0 += rxData0.decode('utf-8', 'replace')
        if (rxData0.decode('utf-8', 'ignore') == '\n'):
            rfm9x.send(bytes("Message from UART0: ", rxString0))
            rxString0 = ""
        rxString1 += rxData1.decode('utf-8', 'replace')
        if (rxData1.decode('utf-8', 'ignore') == '\n'):
            rfm9x.send(bytes("Message from UART1: ", rxString1))
            rxString1 = ""
            
    time.sleep(0.01)
