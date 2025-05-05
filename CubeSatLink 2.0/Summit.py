# CubeSatLink Flight Transceiver Node (Summit)
# Connect to antenna before plug any power in
# Author: Tri Do

import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Initialize UART bus
uart0 = busio.UART(board.TX, board.RX, baudrate=9600, bits = 8, parity = None, timeout=0)
uart1 = busio.UART(board.D24, board.D25, baudrate=9600, bits = 8, parity = None, timeout=0)
message_started = False

# set the time interval (seconds) for sending packets
transmit_interval = 3

# Define radio parameters.
RADIO_FREQ_MHZ = 902.0

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
rfm9x.spreading_factor = 8
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800
rfm9x.ack_delay = 0.1		# set delay before sending ACK
rfm9x.node = 1				# set node addresses
rfm9x.destination = 2

# initialize counter
cnt = 0
NoAck_cnt = 0
# initialize flag and timer
time_now = time.monotonic()
tnow = time.monotonic()
uart0_now=time.monotonic()
text2send = ""

# send startup message from my_node
rfm9x.send_with_ack(bytes("startup message from node {}".format(rfm9x.node), "UTF-8"))
print("Waiting for packets...")

def Blink_Status_LED():
    # Status LED blink every loop
    led.value = not led.value
    tnow=time.monotonic()
    
def UART_Tx(uart,msg):
    if (msg != None):
        uart.write(bytes(msg, 'utf-8'))
        print("({}). UART transmitting: {}".format(len(msg), msg))
    else:
        print('No UART Tx Message...')
def UART_Rx(uart):
    char_buffer = bytearray()
    rx_string = bytearray()
    while uart.in_waiting > 0:
        char_buffer = uart.read(1)
        rx_string = rx_string + char_buffer
    if rx_string.decode('utf-8','replace') != '':			#not empty
        return rx_string.decode('utf-8','ignore')
        
def RFM_Tx(msg, counter, ack_failed_counter):
    counter += 1
    print("Airing received messages from to GroundBLV")
    if not rfm9x.send_with_ack(
        bytes("Summit2: " + msg, "UTF-8")
    ):
        ack_failed_counter += 1
        print(" No Ack: ", counter, ack_failed_counter)
        
def RFM_Rx():
    # Look for packet. Print header, payload, RSSI, SNR
    packet = rfm9x.receive(with_ack=True, with_header=True)
    if packet is not None:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        return packet[4:]
        

while True:
    # try:
    Blink_Status_LED()
    uplink_message = RFM_Rx()
    # uplink_message = "Summit checking in. Behind Great Ideas. Phytecsssss.\n"
    print(uplink_message)
    
    text2send = UART_Rx(uart0)
    receiving2 = UART_Rx(uart1)
    if (text2send == None):
        #UART Receive
        text2send = "no message from UART"
    print(text2send)
    if (receiving2 == None):
        #UART Receive
        receiving2 = "no message"
    print('Receiving2:',receiving2)
    
    if (time.monotonic() - uart0_now > transmit_interval):
        # UART Transmit. send a message every [transmit_interval] seconds. will be gone when uplink is implemented
        uart_now = time.monotonic()
        UART_Tx(uart0,uplink_message)
        msg2 = "testing uart2"
        UART_Tx(uart1,msg2)

    if time.monotonic() - time_now > transmit_interval:
        # send reading after any packet received
        time_now = time.monotonic()
        RFM_Tx(text2send, cnt, NoAck_cnt)
        print('--------------RFM Tx----------------')
        
    time.sleep(0.1)
        
    # except Exception as e:
    #     print(e)
