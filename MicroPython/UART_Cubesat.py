from machine import Pin, UART
from utime import sleep_ms

led = Pin("LED", Pin.OUT)
uart = UART(1, 9600, tx=Pin(4), rx=Pin(5), bits = 8, parity = None, stop=1)
readMessage = bytearray()
nani = bytearray(1)

uart0=UART(0,baudrate=9600, bits=8, parity=None, stop=1, rx=Pin(1), tx=Pin(0))
uart1=UART(1, baudrate=9600, bits=8, parity=None, stop=1, rx=Pin(5), tx=Pin(4))

SendData = bytearray("hahah nice joke bro but I'm currently working so shut up bruh can u omg how long actually is this sentence\n", "utf-8")
SendData1 = bytearray("This is from UART1, but I just wanted to test out how long it can actually be before it cut off or whatever bruh idk\n", "utf-8")
while (True):
    led.toggle()
    uart0.write(SendData)
    sleep_ms(10)
    uart1.write(SendData1)
    sleep_ms(500)
    RecData = uart0.read()
    print(RecData)
    RecData = uart1.read()
    print(RecData)