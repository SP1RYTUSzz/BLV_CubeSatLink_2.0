# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of sending and recieving data with the RFM95 LoRa radio.
# Author: Tony DiCola
import board
import busio
import digitalio
from adafruit_datetime import datetime
import time
import adafruit_rfm9x
import os    # To utilize file operations

from board import *
from adafruit_bus_device.spi_device import SPIDevice


with busio.SPI(SCK, MOSI, MISO) as spi_bus:
    
    cs = digitalio.DigitalInOut(D9)
    device = SPIDevice(spi_bus, cs)

    

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.D5)
RESET = digitalio.DigitalInOut(board.D6)
# Or uncomment and instead use these if using a Feather M0 RFM9x board and the appropriate
# CircuitPython build:
#CS = digitalio.DigitalInOut(board.RFM9X_CS)
#RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Define the onboard LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
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

while True:
    packet2 = (rfm9x.send(input(bytes("Enter passkey...", "utf-8"))))
    
    # File Operation:
    with open('TEST_INTRO.txt', 'r') as f:
        fileToSend = f.read()
        packet3 = (rfm9x.send(bytes(fileToSend, "utf-8")))
        
    print("Sent message 1.")
    time.sleep(2)
    output_time = datetime.now()
    print("Message sent at:", output_time)
    
    tx_data = 0x13
    rx_data = bytearray(1)
    while not spi.try_lock():
        pass
    try:
        spi.configure(baudrate=1000000)
        cs.value = False
        spi.readinto(rx_data)
        cs.value = True
        #spi.init()
    finally:
        spi.unlock()
    
    try:
        rx_raw_string += rx_data.decode("utf-8", "replace")
        
        if rx_data.decode("utf-8") == "\n":
            packet3 = (rfm9x.send(bytes(rx_raw_string, "utf-8")))
            print(rx_raw_string)
            rx_raw_string = ""
            
    except:
        pass
        
        
#----------------------------------------
