# BLV Flight Transceiver (Summit).

import board
import busio
import digitalio
from adafruit_datetime import datetime
import time
import adafruit_rfm9x
import os    # To utilize file operations

from board import *
from adafruit_bus_device.spi_device import SPIDevice

#Turn off Pico on startup then turn on when RFM finish init
"""
pico_en = digitalio.DigitalInOut(board.D24)
pico_en.direction = digitalio.Direction.OUTPUT
pico_en.value = False
"""
# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

#These are for RFM9x, not SPI Pico
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)

cs = digitalio.DigitalInOut(D25)		#for SPI cs
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

# Define the onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

#init SPI
"""
with busio.SPI(SCK, MOSI, MISO) as spi_bus:
    cs = digitalio.DigitalInOut(D25)
    device = SPIDevice(spi_bus, cs)
"""
# Initialize SPI bus.y
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
rfm9x.tx_power = 23 #power: 13dB default, 23dB max

#Starting Tri's code
#allocate memory
tx_string0 = "This is from UART0 channel\n"
tx_string1 = "Speaking to UART1\n"
rx_string0 = ""
rx_string1 = ""
tx_data0 = bytearray(1)
rx_data0 = bytearray(1)
tx_data1 = bytearray(1)
rx_data1 = bytearray(1)
rx_list0 = []
rx_list1 = []
rx_0_index = 0
rx_1_index = 0
selection = bytearray(1)    #see which UART Pico is receiving and relaying from
i0 = 0       #index for time message repeated
i1 = 0
flag0 = False
flag1 = False
unicode_error_occurence = 0

MAX_BUF = 255
while True:
    """
    #RECEIVE SECTION
    packet = rfm9x.receive()
    if packet is None:
        print("Received nothing!")
    else:
        print("Received (ASCII): {0}".format(str(packet, "ascii")))
        print("RSSI: {0} dB, SNR: {1} dB.".format(rfm9x.last_rssi, rfm9x.last_snr))
    
    #This delay is to help rfm push the send before receiving
    time.sleep(0.04)
    """
    while not spi.try_lock():
        pass
    try:
        spi.configure(baudrate=1000000)
    finally:
        spi.unlock()
        
    try:
        # Keep putting in new message after tx_string run out
        if (tx_string0 == ""):
            tx_string0 = "uart0 repeat time " + str(i0) + "\n"
            i0 += 1
        if (i0 >= 10000):
            i0 = 0
        if (tx_string1 == ""):
            tx_string1 = "uart1 repeating time " + str(i1) + "\n"
            i1 += 1
        if (i1 >= 10000):
            i1 = 0
        
        # SPI ENCODE: split tx_string into 1 byte chunk
        if tx_string0:
            tx_data0 = bytearray(tx_string0[0:1], "utf-8", "ignore")
            tx_string0 = tx_string0[1:]  # len(tx_string)-1 if sht happened
        if tx_string1:
            tx_data1 = bytearray(tx_string1[0:1], "utf-8", "ignore")
            tx_string1 = tx_string1[1:]  # len(tx_string)-1 if sht happened

        
        while not spi.try_lock():
            pass
        try:
            spi.configure(baudrate=1000000)
            # SPI EXCHANGE: conversation, 1 byte per cs cycle
            cs.value = False
            spi.write_readinto(b'#', selection)
            cs.value = True
            #print(selection)
            if (selection == b'`'):			#
                cs.value = False
                spi.write_readinto(tx_data0, rx_data0)
                cs.value = True
                cs.value = False
                spi.write_readinto(tx_data1, rx_data1)
                cs.value = True
                #print(rx_data0, rx_data1)
                if rx_data0 != b'\x00':
                    rx_list0.append(rx_data0.decode('utf-8', 'ignore'))
                    rx_0_index += 1
                if rx_data1 != b'\x00':
                    rx_list1.append(rx_data1.decode('utf-8', 'ignore'))
                    rx_1_index += 1
                #print(selection, rx_data0, rx_data1)
                if rx_data0.decode('utf-8', 'ignore') == '\n':
                    flag0 = True
                    rx_string0 = ''.join(rx_list0)
                    print("Message from UART0: ", rx_string0)
                    led.value = not led.value
                    rx_0_index = 0
                if rx_data1.decode('utf-8', 'ignore') == '\n':
                    flag1 = True
                    rx_string1 = ''.join(rx_list1)
                    print("Message from UART1: ", rx_string1)
                    led.value = not led.value
                    rx_1_index = 0

                # print(rx_data0, rx_data1)
        finally:
            spi.unlock()
        if flag0 == True:
            rfm9x.send(bytes("UART0: "+rx_string0, 'utf-8'))
            rx_list0 = []
            flag0 = False
        if flag1 == True:
            rfm9x.send(bytes("UART1: "+rx_string1, 'utf-8'))
            rx_list1 = []
            flag1 = False

    except UnicodeError:
        print("Unicode Error time ", unicode_error_occurence)
        unicode_error_occurence += 1
