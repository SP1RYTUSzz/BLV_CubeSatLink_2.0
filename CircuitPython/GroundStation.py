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
try:
    sdcard = sdcardio.SDCard(spi, CS_SD)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
except OSError as e:
    print("ERROR: SD CARD INIT FAILED, NO SD MOST LIKELY")
# Initialize RFM95
rfm9x = adafruit_rfm9x.RFM9x(spi, CS_RFM, RESET, RADIO_FREQ_MHZ, agc = True)


# Radio config
rfm9x.tx_power = 23
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800
rfm9x.spreading_factor = 7		#higher = lower bitrate
rfm9x.enable_crc = True	# enable CRC checking
rfm9x.ack_delay = 0.1	# set delay before transmitting ACK (seconds)
rfm9x.node = 2			# set node addresses
rfm9x.destination = 1	# set destination addresses

# initialize program counters & timer
counter = 0
ack_failed_counter = 0
t_led = 0

# Wait to receive packets.
print("Waiting for packets...")
while True:
    # Status LED blink
    if (time.monotonic() - t_led > 0.5):
        led.value = not led.value
        t_led=time.monotonic()
    
    # Look for a new packet: only accept if addresses to my_node
    packet = rfm9x.receive(with_ack=True, with_header=True)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        # Write received data to SD
        try:
            with open("/sd/DownlinkData.txt", "a") as f:		#a for append, w for write
                f.write(str(counter).encode()+". "+packet[4:])	#formatting in term of #. [Message]
                f.flush()
                print("Message wrote to SD")
        except OSError as e:
            print("SD Card write error")
        counter += 1
        # send a  mesage to destination_node from my_node
        if not rfm9x.send_with_ack(
            bytes("response from GroundBLV {}".format(rfm9x.node, counter), "UTF-8")
        ):
            ack_failed_counter += 1
            print(" No Ack: ", counter, ack_failed_counter)
