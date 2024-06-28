# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple demo of sending and recieving data with the RFM95 LoRa radio.
# Author: Tony DiCola
import board
import busio
import digitalio
import time
import adafruit_rfm9x


# Define radio parameters.
RADIO_FREQ_MHZ = 437.4  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
# Or uncomment and instead use these if using a Feather M0 RFM9x board and the appropriate
# CircuitPython build:
# CS = digitalio.DigitalInOut(board.RFM9X_CS)
# RESET = digitalio.DigitalInOut(board.RFM9X_RST)

# Define the onboard LED
LED = digitalio.DigitalInOut(board.D13)
LED.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initialze RFM radio

rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# Note that the radio is configured in LoRa mode so you can't control sync
# word, encryption, frequency deviation, or other settings!

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.spreading_factor=8
rfm9x.timeout=10
rfm9x.tx_power = 23
rfm9x.node=0xfa
rfm9x.destination=0xfb

# Send a packet.  Note you can only send a packet up to 252 bytes in length.
# This is a limitation of the radio packet size, so if you need to send larger
# amounts of data you will need to break it into smaller send calls.  Each send
# call will wait for the previous one to finish before continuing.


# Wait to receive packets.  Note that this library can't receive data at a fast
# rate, in fact it can only receive and process one 252 byte packet at a time.
# This means you should only use this for low bandwidth scenarios, like sending
# and receiving a single message at a time.


print("Waiting for packets...")


signal_status_message = "KN6NAQ!CMD69"
# Corresponds with BLV code that sends us back the RSSI, or signal status

alt_status_message = "KN6NAQ!CMD70"
# Corresponds with BLV code that sends us back the altitude info

coord_status_message = "KN6NAQ!CMD71"
# Corresponds with BLV code that sends us back the coordinate info
# aka latitude and longitude

cut_away_message = "KN6NAQ!CMD65"
#cut_away_message = "HELLOW0RLD23"

send_that_shit = "bet" # defines a new variable to activate cutaway

def send_message(msg):
    rfm9x.send(msg)
    print(f"Sending message: {msg}")
    time.sleep(1) # slight delay for user experience lol


while True:
    
    packet = None

    send_that_shit = input("""
=============================
Options:
[1] Get signal status
[3] Get current altitude
[5] Get current coordinates
[9] Manually activate cutaway
=============================
Enter your choice: 
""")

    if send_that_shit == "1":
        send_message(signal_status_message)
    
    elif send_that_shit == "3":
        send_message(alt_status_message)

    elif send_that_shit == "5":
        send_message(coord_status_message)

    elif send_that_shit == "9":
        send_message(cut_away_message)


    packet = rfm9x.receive()
    # Optionally change the receive timeout from its default of 0.5 seconds:
    # packet = rfm9x.receive(timeout=5.0)
    # If no packet was received during the timeout then None is returned.

    if send_that_shit != "1" and send_that_shit != "3" and send_that_shit != "5" and send_that_shit != "9":
        print("Invalid response.")
        time.sleep(2)
        # this way, if an invalid response is entered, the "Received nothing!" line won't be printed
    else:
        if packet is None:
            # Packet has not been received
            LED.value = False
            print("Received nothing! Listening again...")
        else:
            # Received a packet!
            LED.value = True
                # Print out the raw bytes of the packet:
            print("Received (raw bytes): {0}".format(packet))
                # And decode to ASCII text and print it too.  Note that you always
                # receive raw bytes and need to convert to a text format like ASCII
                # if you intend to do string processing on your data.  Make sure the
                # sending side is sending ASCII data before you try to decode!
            packet_text = str(packet, "ascii")
            print("Received (ASCII): {0}".format(packet_text))
                # Also read the RSSI (signal strength) of the last received message and
                # print it.
            rssi = rfm9x.last_rssi
            print("Received signal strength: {0} dB".format(rssi))

            time.sleep(2)






