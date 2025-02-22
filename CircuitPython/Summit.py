# CubeSatLink Flight Transceiver Node (Summit)
# Connect to antenna before plug any power in
# Author: Tri Do

import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Initialize UART bus
uart = busio.UART(board.TX, board.RX, baudrate=9600, bits = 8, parity = None, timeout=0)
message_started = False
uplink_message = "Summit checking in with a long message here bro whatever should I write in here. Behind Great Ideas.\n"
uart_char_buffer = bytearray()
uart_rx_string = bytearray()



# Define radio parameters.
RADIO_FREQ_MHZ = 902.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip.
# set GPIO pins as necessary -- this example is for Raspberry Pi
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, agc = True)

# rfm9x post-config
rfm9x.enable_crc = True
rfm9x.tx_power = 23
rfm9x.spreading_factor = 7
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800
rfm9x.ack_delay = 0.1		# set delay before sending ACK
rfm9x.node = 1				# set node addresses
rfm9x.destination = 2

# initialize counter
counter = 0
ack_failed_counter = 0
# initialize flag and timer
transmit_interval = 5			# set the time interval (seconds) for sending packets
time_now = time.monotonic()
tnow = time.monotonic()
uart_now=time.monotonic()
text2send = ""
Packet_length = 100

# send startup message from my_node
rfm9x.send_with_ack(bytes("startup message from node {}".format(rfm9x.node), "UTF-8"))
print("Waiting for packets...")


while True:
     # Status LED blink
    if (time.monotonic() - tnow > 0.25):
        led.value = not led.value
        tnow=time.monotonic()
    # Look for a new packet: only accept if addresses to my_node
    packet = rfm9x.receive(with_ack=True, with_header=True)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        
    # Break the packet down to each customer
    

    #UART Receive
    while uart.in_waiting > 0:
        uart_char_buffer = uart.read(1)
        uart_rx_string = uart_rx_string + uart_char_buffer
        #	print(uart_rx_string)
    if uart_rx_string.decode('utf-8', 'ignore') != '':
        text2send = uart_rx_string.decode('utf-8', 'ignore')
        new_UART_RX = True
        uart_rx_string = bytearray()
        print("UART RX:", text2send)
        
    # UART Transmit
    if (time.monotonic() - uart_now > transmit_interval):
        uart_now = time.monotonic()
        uart.write(uplink_message)
        print("Sent to UART device")

    # send reading after any packet received
    if time.monotonic() - time_now > transmit_interval:
        # reset timer
        time_now = time.monotonic()
        counter += 1
        new_UART_RX = False
        # break down long Student UART code to not overflow RFM
        for i in range(0, len(text2send), Packet_length):
            # send a  mesage to destination_node from my_node
            if not rfm9x.send_with_ack(
                bytes("Summit2: " + text2send[i:i+Packet_length], "UTF-8")
            ):
                ack_failed_counter += 1
                print(" No Ack: ", counter, ack_failed_counter)
        print("Sent UART RX to GroundBLV")
        print('---------------------')
