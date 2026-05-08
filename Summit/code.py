# CubeSatLink Flight Transceiver Node (Summit)
# Connect to antenna before plug any power in
# Author: Tri Do

import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Initialize UART bus
uart0 = busio.UART(board.GP0, board.GP1, baudrate=9600, bits = 8, parity = None, timeout=1)
uart1 = busio.UART(board.GP4, board.GP5, baudrate=9600, bits = 8, parity = None, timeout=1)
message_started = False



# Define pins connected to the chip.
# set GPIO pins as necessary -- this example is for Raspberry Pi
CS = digitalio.DigitalInOut(board.GP17)
RESET = digitalio.DigitalInOut(board.GP21)
# GPIO to enable PA & LNA
RF_RXEN = digitalio.DigitalInOut(board.GP23)
RF_RXEN.direction = digitalio.Direction.OUTPUT
RF_TXEN = digitalio.DigitalInOut(board.GP24)
RF_TXEN.direction = digitalio.Direction.OUTPUT
# Status LED
led = digitalio.DigitalInOut(board.GP10)			# This is UART2 LED
led.direction = digitalio.Direction.OUTPUT

# Initialize SPI bus.
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP20)


# Define radio parameters.
RF_RXEN.value = 0;
RF_TXEN.value = 0;

RADIO_FREQ_MHZ = 435.75
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, agc = True)
# rfm9x post-config
rfm9x.enable_crc = True
rfm9x.tx_power = 23
rfm9x.spreading_factor = 7
rfm9x.coding_rate = 6
rfm9x.signal_bandwidth = 125000
rfm9x.ack_delay = 0.1		# set delay before sending ACK
rfm9x.node = 8
rfm9x.destination = 7
# Initialize RFM radio
transmit_interval = 5		# set the time interval (seconds) for sending packets
RFMTimeOut = 10

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
        rx_string = rx_string + char_buffer
    string = ''.join([chr(b) for b in rx_string])
    return string
    #.decode('utf-8','replace') != '':			#not empty
    #    return rx_string.decode('utf-8','ignore')
     
cnt = 0
def incCnt():
    global cnt
    cnt += 1
def dspCnt():
    global cnt
    return cnt
NoAck_cnt = 0
def incNAK():
    global NoAck_cnt
    NoAck_cnt += 1

def petRFMWatchdog():
    global rfmWatchdog
    rfmWatchdog = time.monotonic()
    
def RFM_Tx(cust,msg):
    RF_TXEN.value = 1;
    incCnt()
    full_msg = f"{cust}, {msg}"
    print(f"Airing Downlink with Message: {full_msg}")
    if not rfm9x.send_with_ack(
        bytes(full_msg, "UTF-8")
    ):
        incNAK()
        print("Tx No Ack: ")
    RF_TXEN.value = 0;
        
def RFM_Rx():
    # Look for packet. Print header, payload, RSSI, SNR
    packet = rfm9x.receive(with_ack=True, with_header=True)
    if packet is not None:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}, SNR: {1}".format(rfm9x.last_rssi, rfm9x.last_snr))
        return packet[4:]
        
uartTxInterval = 3
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
        uplink_message = "Summit checking in. Behind Great Ideas. Phytecsssss.\n"
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
