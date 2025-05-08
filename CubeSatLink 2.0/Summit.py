# CubeSatLink Flight Transceiver Node (Summit)
# Connect to antenna before plug any power in
# NOTE: UART Pinout. It is flipped by adafruit design, we can't change it to be logical.
# Author: Tri Do

import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Initialize UART bus
uart0 = busio.UART(board.TX, board.RX, baudrate=9600, bits = 8, parity = None, timeout=1)
uart1 = busio.UART(board.D24, board.D25, baudrate=9600, bits = 8, parity = None, timeout=1)
message_started = False

uartTxInterval = 1
transmit_interval = 5
RFMTimeOut = 10

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

RADIO_FREQ_MHZ = 902.0
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, agc = True)
# rfm9x post-config
rfm9x.enable_crc = True
rfm9x.tx_power = 23
rfm9x.spreading_factor = 8
rfm9x.coding_rate = 8
#rfm9x.signal_bandwidth = 7800
rfm9x.ack_delay = 0.1		# set delay before sending ACK
rfm9x.node = 8
rfm9x.destination = 7

# initialize flag and timer
time_now = 0
tnow = 0
uart_now = 0
rfmWatchdog = 0
uart0_receiving = ""

# send startup message from my_node
rfm9x.send_with_ack(bytes("startup message from node {}".format(rfm9x.node), "UTF-8"))
print("Waiting for packets...")

def Blink_Status_LED():
    # Status LED blink every loop
    led.value = not led.value
    tnow=time.monotonic()
    
def UART_Tx(uart,msg):
    if (msg != None):
        uart.write(msg)
        print("({}). UART transmitting: {}".format(len(msg), msg))
    else:
        print('No UART Tx Message...')
        
def UART_Rx(uart):
    char_buffer = bytearray()
    rx_string = bytearray()
    while uart.in_waiting > 0:
        char_buffer = uart.read(1)
        if (char_buffer == '\n'):
            break
        else:
            rx_string = rx_string + char_buffer
    string = ''.join([chr(b) for b in rx_string])
    return string
    #.decode('utf-8','replace') != '':			#not empty
    #    return rx_string.decode('utf-8','ignore')
     
cnt = 0
def incCnt():
    global cnt
    cnt += 1
def readCnt():
    global cnt
    return cnt
NoAck_cnt = 0
def incNAK():
    global NoAck_cnt
    NoAck_cnt += 1
def readNAK():
    global NoAck_cnt
    return NoAck_cnt

def petRFMWatchdog():
    global rfmWatchdog
    rfmWatchdog = time.monotonic()
    
def RFM_Tx(cust,msg):
    incCnt()
    full_msg = f"{cust}, {msg}"
    print(f"Airing Downlink with Message: {full_msg}")
    if not rfm9x.send_with_ack(
        bytes(full_msg, "UTF-8")
    ):
        incNAK()
        print(f"Tx No Ack: {readCnt()} {readNAK()}")
        
def RFM_Rx():
    # Look for packet. Print header, payload, RSSI, SNR
    packet = rfm9x.receive(with_ack=True, with_header=True)
    if packet is not None:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        return packet[4:]
        
uart0_receiving = ''
uart1_receiving = ''
while True:
    try:
        Blink_Status_LED()
        
        # RFM Tx 
#     	if time.monotonic() - time_now > transmit_interval:
            # send reading after any packet received
        time_now = time.monotonic()
        if (time.monotonic() - rfmWatchdog > RFMTimeOut):
            petRFMWatchdog()
            RFM_Tx('S',"Link healthy, No UART Message")
        if (uart0_receiving != ''):
            petRFMWatchdog()
            cust = 'A'
            RFM_Tx(cust,uart0_receiving)
            uart0_receiving = ''
        if (uart1_receiving != ''):
            petRFMWatchdog()
            cust = 'B'
            RFM_Tx(cust,uart1_receiving)
            uart1_receiving = ''
        
        # UART Rx
        uart0_receiving = UART_Rx(uart0)
        uart1_receiving = UART_Rx(uart1)
        if (uart0_receiving == ''):
            pass
        else:
            print(len(uart0_receiving),'uart0_receiving:',uart0_receiving)
        if (uart1_receiving == ''):
            pass
        else:
            print(len(uart1_receiving),'uart1_receiving:',uart1_receiving)

    #     #RFM Rx
    #     uplink_message = RFM_Rx()
        uplink_message = "Summit checking in. Behind Great Ideas. Phytecssssssadhfkjdshasdh whatever lorem ipsum.\n"
    #     print("RFM Recieved:",uplink_message)
        
        # UART Tx
        if (time.monotonic() - uart_now > uartTxInterval):
            # UART Transmit. send a message every [transmit_interval] seconds. will be gone when uplink is implemented
            uart_now = time.monotonic()
            UART_Tx(uart0,uplink_message)
            msg1 = "testing uart1"
            UART_Tx(uart1,msg1)
            
    #     print("-----END LOOP-----")
        time.sleep(0.1)
            
    except Exception as e:
        print(e)
