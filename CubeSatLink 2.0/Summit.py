# BLV Summit Commit 9/10
#
import time
import board
import busio
import digitalio
import adafruit_rfm9x

# Define radio parameters.
RADIO_FREQ_MHZ = 915.0

CS = digitalio.DigitalInOut(board.D10)
RESET = digitalio.DigitalInOut(board.D11)

# Initialize SPI bus.
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
# Initialze RFM radio
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)

# set delay before transmitting ACK (seconds)
rfm9x.ack_delay = 0.1
# set node addresses
rfm9x.node = 2
rfm9x.destination = 1
# initialize counter
counter = 0
ack_failed_counter = 0

transmit_interval = 1
# Wait to receive packets.
print("Waiting for packets...")
time_now = time.monotonic()
while True:
    # Look for a new packet: only accept if addresses to my_node
    packet = rfm9x.receive(with_ack=True, with_header=True)
    # If no packet was received during the timeout then None is returned.
    if packet is not None:
        # Received a packet!
        # Print out the raw bytes of the packet:
        print("Received (raw header):", [hex(x) for x in packet[0:4]])
        print("Received (raw payload): {0}".format(packet[4:]))
        print("RSSI: {0}".format(rfm9x.last_rssi))
        print("SNR: {0}".format(rfm9x.last_snr))
        # send reading after any packet received
    if time.monotonic() - time_now > transmit_interval:
        # reset timeer
        time_now = time.monotonic()
        counter += 1
        # send a  mesage to destination_node from my_node
        if not rfm9x.send_with_ack(
            bytes("message from Summit. (Node {}, count# {})".format(rfm9x.node, counter), "UTF-8")
        ):
            ack_failed_counter += 1
            print(" No Ack: ", counter, ack_failed_counter)

