# CubeSatLink Flight Transceiver Node (Summit)
# Connect to antenna before plug any power in
# Author: Tri Do
#
import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Initialize UART bus
uart = busio.UART(board.TX, board.RX, baudrate=9600, bits = 8, parity = None, timeout=0)
message_started = False
uplink_message = "ur gey"
uart_char_buffer = bytearray()
uart_rx_string = bytearray()

# set the time interval (seconds) for sending packets
transmit_interval = 5

# Define radio parameters.
RADIO_FREQ_MHZ = 902.0  # Frequency of the radio in Mhz. Must match your
# module! Can be a value like 915.0, 433.0, etc.

# Define pins connected to the chip.
# set GPIO pins as necessary -- this example is for Raspberry Pi
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, agc = True)

# enable CRC checking
rfm9x.enable_crc = True
rfm9x.tx_power = 23
rfm9x.spreading_factor = 9
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800

# set delay before sending ACK
rfm9x.ack_delay = 0.1
# set node addresses
rfm9x.node = 1
rfm9x.destination = 2
# initialize counter
counter = 0
ack_failed_counter = 0
# send startup message from my_node
rfm9x.send_with_ack(bytes("startup message from node {}".format(rfm9x.node), "UTF-8"))

# Wait to receive packets.
print("Waiting for packets...")
# initialize flag and timer
time_now = time.monotonic()
uart_now=time.monotonic()

while True:
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
    

    # UART Transmit
    if (time.monotonic() - uart_now > transmit_interval):
        uart_now = time.monotonic()
        uart.write(uplink_message)
        print("Sent '{}' to UART device".format(uplink_message))
    #UART Receive
    while uart.in_waiting > 0:
        uart_char_buffer = uart.read(1)
        uart_rx_string = uart_rx_string + uart_char_buffer
        print(uart_rx_string)
    if uart_rx_string != None:
        #buffer = uart_rx_string.decode(encoding = 'utf-8', errors = 'ignore')
        uart_rx_string = bytearray()

    # send reading after any packet received
    if time.monotonic() - time_now > transmit_interval:
        # reset timeer
        time_now = time.monotonic()
        counter += 1
        # send a  mesage to destination_node from my_node
        if not rfm9x.send_with_ack(
            bytes("message from node node {} {}".format(rfm9x.node, counter), "UTF-8")
        ):
            ack_failed_counter += 1
            print(" No Ack: ", counter, ack_failed_counter)
