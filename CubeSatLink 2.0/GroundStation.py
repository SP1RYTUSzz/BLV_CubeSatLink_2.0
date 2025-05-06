# CubeSatLink Ground Node (GroundStation)
# Connect to antenna before plug any power in
# Author: Tri Do
#
import time
import board
import busio
import digitalio
import adafruit_rfm9x
import sdcardio
import storage

# FIELD CONFIG PARAMETERS
RADIO_FREQ_MHZ = 902.0

# Declare SPI pins
RESET = digitalio.DigitalInOut(board.D11)
CS_RFM = digitalio.DigitalInOut(board.D10)
CS_SD = board.D4
# Declare on-board LED status blink
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


# Initialize SPI bus 
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
# Initialize SD Card Module

# Initialize RFM95
rfm9x = adafruit_rfm9x.RFM9x(spi, CS_RFM, RESET, RADIO_FREQ_MHZ, agc = True)


# Radio config
rfm9x.tx_power = 23
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800
rfm9x.spreading_factor = 8		#higher = lower bitrate
rfm9x.enable_crc = True	# enable CRC checking
rfm9x.ack_delay = 0.1	# set delay before transmitting ACK (seconds)
rfm9x.node = 2			# set node addresses
rfm9x.destination = 1	# set destination addresses

tnow = 0
TxInterval = 5

def SD_Init():
    try:
        sdcard = sdcardio.SDCard(spi, CS_SD)
        vfs = storage.VfsFat(sdcard)
        storage.mount(vfs, "/sd")
        # Write headers for the SD Card data
        with open("/sd/Dev.csv", "a") as f:		#a for append, w for write
            f.write("\n-----------STARTED-------------\n")	#formatting in term of #. [Message]
            f.write("time (ms),GroundStation cnt,Summit cnt,CubeSat #,RSSI,SNR, Message\n")
            f.flush()
            print("SD Headers wrote to Dev.csv")
        for cust in range(3):
            with open(f"/sd/Cube{cust}Data.csv", "a") as f:		#a for append, w for write
                f.write("\n-----------STARTED-------------\n")	#formatting in term of #. [Message]
                f.write("Count 1,Count 2,CubeSat #, Message\n")
                f.flush()
                print("SD Headers wrote to File:", f"Cube{cust}Data.csv")
    except OSError as e:
        print("ERROR: SD CARD INIT FAILED, NO SD MOST LIKELY")
        
def SD_Write_Customer(fileName,packet):
    try:
        with open(fileName, "a") as f:		#a for append, w for write
            f.write(
                "{}, {}, {}, Msg:, {}\n".format(
                    hex(counter),
                    hex(packet[2]),
                    hex(packet[4]),
                    ''.join([chr(b) for b in packet[5:]])		#packet[4:], decoded from bytearray to str
                )
            )
            f.flush()
            print("Message wrote to SD file ", fileName)
    except OSError as e:
        print("SD Card write error at Customer. Is SD Card loose?")

def SD_Write_Dev(packet):
    try:
        with open("/sd/Dev.csv", "a") as f:		#a for append, w for write
            f.write(
                "{}, {}, {}, {}, {}, {}, Msg:, {}\n".format(
                    round(time.monotonic(),3),
                    hex(counter),
                    hex(packet[2]),
                    hex(packet[4]),
                    rfm9x.last_rssi,
                    rfm9x.last_snr,
                    ''.join([chr(b) for b in packet[4:]])		#packet[4:], decoded from bytearray to str
                )
            )
            f.flush()
            print("Message wrote to SD file Dev.csv")
    except OSError as e:
        print("SD Card write error at Dev. Is SD Card loose?")
counter = 0
def incCnt():
    global counter
    counter += 1
    
ack_failed_counter = 0
def incNAK():
    global ack_failed_counter
    ack_failed_counter += 1

def RFM_Tx(msg):
    print("Airing Uplink")
    if not rfm9x.send_with_ack(
        bytes(msg, "UTF-8")
    ):
        incCnt()
        incNAK()
        print("Tx No Ack: ", counter, ack_failed_counter)
            
def RFM_Rx():
    packet = rfm9x.receive(with_ack=True, with_header=True)
    if packet is not None:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        SD_Write_Dev(packet)
        if packet[4] == 0x41:
            SD_Write_Customer("/sd/Cube0Data.csv",packet)
        elif packet[4] == 0x42:
            SD_Write_Customer("/sd/Cube1Data.csv",packet)
        elif packet[4] == 0x43:
            SD_Write_Customer("/sd/Cube2Data.csv",packet)
        elif packet[4] == 0x53:
            SD_Write_Dev(packet)
            print("Double written to Dev.csv")
        else:
            print("SD Write Destination Error. Missing Destination Header packet[4]! Check flight transceiver")
        incCnt()
        
    
def Blink_Status_LED():
    # Status LED blink every loop
    led.value = not led.value
    tnow=time.monotonic()

##### maybe implement more robust LED?
# START ROUTINE
SD_Init()
print("Waiting for packets...")
while True:
    Blink_Status_LED()
#     if (time.monotonic() - tnow > TxInterval):
#         tnow = time.monotonic()
#         Tx_message = "GroundBLV checking {}".format(rfm9x.node, counter)
#         RFM_Tx(Tx_message)
    RFM_Rx()
    time.sleep(0.1)
