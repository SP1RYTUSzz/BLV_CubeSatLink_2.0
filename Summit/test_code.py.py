# code.py
import time
import board
import busio
import digitalio
import microcontroller
import adafruit_ina260
import adafruit_mcp9808

#dir(board)

# Initialize I2C bus
i2c = busio.I2C(scl = microcontroller.pin.GPIO29, sda = microcontroller.pin.GPIO28)

# Initialize the INA260 sensor
# The default I2C address is 0x40
ina260 = adafruit_ina260.INA260(i2c)
mcp = adafruit_mcp9808.MCP9808(i2c)
  

# Edit these for your board/wiring
SCK = board.GP14
MOSI = board.GP15
MISO = board.GP12
CS_PIN = board.GP13

# Edit these for your chip
BAUDRATE = 1_000_000
POLARITY = 0
PHASE = 0

# Many SPI sensors use bit 7 = 1 for read.
# Example: WHO_AM_I register at 0x0F becomes 0x8F.
WHO_AM_I_REG = 0x0F
READ_MASK = 0x80
EXPECTED_ID = None  # set to e.g. 0x68, 0x71, etc. if known

spi = busio.SPI(SCK, MOSI, MISO)

cs = digitalio.DigitalInOut(CS_PIN)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True


def spi_read_register(reg):
    while not spi.try_lock():
        pass

    try:
        spi.configure(
            baudrate=BAUDRATE,
            polarity=POLARITY,
            phase=PHASE,
        )

        tx = bytearray([reg | READ_MASK, 0x00])
        rx = bytearray(2)

        cs.value = False
        spi.write_readinto(tx, rx)
        cs.value = True

        return rx[1]

    finally:
        spi.unlock()


while True:
    value = spi_read_register(WHO_AM_I_REG)

    if EXPECTED_ID is None:
        print("SPI response: 0x%02X" % value)
    elif value == EXPECTED_ID:
        print("SPI device OK: 0x%02X" % value)
    else:
        print("Unexpected response: got 0x%02X, expected 0x%02X" %
              (value, EXPECTED_ID))
    
    # Read and print the sensor values
    print("Current: %.2f mA" % ina260.current)
    print("Voltage: %.2f V" % ina260.voltage)
    print("Power:   %.2f mW" % ina260.power)
    print("-" * 20)
    print('Temperature: {} degrees C'.format(mcp.temperature))
  

    time.sleep(1)
