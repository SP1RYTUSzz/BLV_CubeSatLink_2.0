# BLV Ground Station

import board
import busio
import digitalio
import time
# import sdcardio
# import storage

import adafruit_rfm9x



# Define radio parameters.
RADIO_FREQ_MHZ = 915.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip, use these if wiring up the breakout according to the guide:
cs_RFM = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
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
rfm9x = adafruit_rfm9x.RFM9x(spi, cs_RFM, RESET, RADIO_FREQ_MHZ)

# Note that the radio is configured in LoRa mode so you can't control sync
# word, encryption, frequency deviation, or other settings!

# You can however adjust the transmit power (in dB).  The default is 13 dB but
# high power radios like the RFM95 can go up to 23 dB:
rfm9x.tx_power = 23

# Wait to receive packets.  Note that this library can't receive data at a fast
# rate, in fact it can only receive and process one 252 byte packet at a time.
# This means you should only use this for low bandwidth scenarios, like sending
# and receiving a single message at a time.
print("Waiting for packets...")

# # SET UP MICROSD BREAKOUT BOARD
# cs_SD = board.D25  # Chip select pin for SD card
# sdcard = sdcardio.SDCard(spi, cs_SD)
# vfs = storage.VfsFat(sdcard)
# storage.mount(vfs, "/sd")

# # SET UP MICRO_SD BREAKOUT BOARD
# # Define GPIO pin for microSD card breakout board
# cs_SD = board.D1
# # Add a delay before initializing the microSD card
# time.sleep(1)
# # Create the microSD card object and the filesystem object
# sdcard = sdcardio.SDCard(spi, cs_SD)
# vfs = storage.VfsFat(sdcard)
# # Finally, mount the microSD card's filesystem into the CircuitPython filesystem.
# storage.mount(vfs, "/sd")

while True:
    packet = rfm9x.receive()
    My_Data=(packet)
    # Optionally change the receive timeout from its default of 0.5 seconds:
    # packet = rfm9x.receive(timeout=5.0)
    # If no packet was received during the timeout then None is returned.


    if packet is None:
        # Packet has not been received
        led.value = False
        print("DOWNLINK: Received nothing! Listening again...")
        print("-"*80)
        time.sleep(1)

        # # for testing the SD card reader
        # try: 
        #     with open('/sd/data.txt', 'a') as file:
        #     # write some data to the file
        #         file.write("End my suffering")
        #     # print a message to confirm that the data was written
        #     print('Data written to flash memory.')
            
        #     # Check if data was written to SD card
        #     with open('/sd/data.txt', 'r') as file:
        #         written_data = file.seek(0,2)  # Seek to end of file (last written data)
        #         if written_data == "End my suffering":
        #             print('Data successfully written to SD card.')
        #         else:
        #             print('Error: Data not written to SD card correctly.')
        # except OSError as e:
        #     print(f"Error writing data to SD card: {e}")

    else:
        # Received a packet!
        led.value = True
        # Print raw bytes of the packet:
        print("DOWNLINK: Received (raw bytes): {0}".format(packet))
        packet_text = str(packet, "ascii")
        print("Received (ASCII): {0}".format(packet_text))
        # Prin RSSI and SNR
        rssi = rfm9x.last_rssi
        snr = rfm9x.last_snr
        print("Received signal strength: {0} dB".format(rssi), ", SNR: {0} dB".format(snr))
        print("-"*80)
        
        
        # storage.remount('/', readonly=False)

        # # open the flash memory for reading and writing
        # try: 
        #     with open('/sd/data.txt', 'a') as file:
        #     # write some data to the file
        #         #file.write(f"{My_Data}\n")
        #         file.write(f"{packet}\n")
        #     # print a message to confirm that the data was written
        #     print('Data written to flash memory.')
            
            
        #     # Check if data was written to SD card
        #     with open('/sd/data.txt', 'r') as file:
        #         written_data = file.seek(0,2)  # Seek to end of file (last written data)
        #         if written_data == f"{packet}":
        #             print('Data successfully written to SD card.')
        #         else:
        #             print('Error: Data not written to SD card correctly.')
        # except OSError as e:
        #     print(f"Error writing data to SD card: {e}")

        # storage.remount('/', readonly=True)
    """
        
    #------------------------------------------------------
    #STARTING RFM SEND SECTION
    send_msg = "Hello from Ground  Station!\n"
    rfm9x.send(bytes(send_msg, "utf-8"))
    print("Sent Hello message")
    """
        
    time.sleep(0.05)
