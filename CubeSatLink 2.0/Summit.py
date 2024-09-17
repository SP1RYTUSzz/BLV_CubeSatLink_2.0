# BLV Summit Flight Transceiver
import time
import board
import busio
import digitalio
import adafruit_rfm9x


# Initialize UART bus
uart = busio.UART(board.A2, board.A3, baudrate=9600, bits = 8, parity = None, timeout = 10)

# Initialize SPI bus & RFM Radio
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)
RADIO_FREQ_MHZ = 927.0
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# rfm9x settings
rfm9x.ack_delay = 0.1
rfm9x.node = 2
rfm9x.destination = 1
counter = 0
ack_failed_counter = 0

rfm9x.tx_power = 23
#rfm9x.signal_bandwidth = 62500
#rfm9x.coding_rate = 6
rfm9x.spreading_factor = 7
rfm9x.enable_crc = True

transmit_interval = 1


# Wait to receive packets.
print("Waiting for packets...")
time_now = time.monotonic()
while True:
    
    
    packet = rfm9x.receive(with_ack=True, with_header=True)
    # print after any packet received
    if packet is not None:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}".format(rfm9x.last_rssi))
        print("SNR: {0}".format(rfm9x.last_snr))
        
    # send a mesage to destination_node from my_node
    if time.monotonic() - time_now > transmit_interval:
        time_now = time.monotonic()
        counter += 1
        # error
        if not rfm9x.send_with_ack(
            bytes("message from Summit. (Node {}, count# {})".format(rfm9x.node, counter), "UTF-8")
        ):
            ack_failed_counter += 1
            print(" No Ack: ", counter, ack_failed_counter)

