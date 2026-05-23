import time
import board
import busio
import digitalio
from adafruit_bus_device.spi_device import SPIDevice

SCK = board.GP14
MOSI = board.GP15
MISO = board.GP12
CS_PIN = board.GP13

spi = busio.SPI(
    clock=SCK,
    MOSI=MOSI,
    MISO=MISO
)

cs = digitalio.DigitalInOut(CS_PIN)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

device = SPIDevice(
    spi,
    cs,
    baudrate=1000000,
    polarity=0,
    phase=0
)

BUF_LEN = 128
line_buffer = ""
while True:
    rx = bytearray(BUF_LEN)
    tx = bytearray([0xFF] * BUF_LEN)

    with device as spi_dev:
        spi_dev.write_readinto(tx, rx)

    useful = bytes(b for b in rx if b not in (0xFF, 0x00))

    if useful:
        text = useful.decode("ascii", "ignore")
        line_buffer += text

        while "\r\n" in line_buffer:
            line, line_buffer = line_buffer.split("\r\n", 1)
            if line:
                print(line)


    time.sleep(1)