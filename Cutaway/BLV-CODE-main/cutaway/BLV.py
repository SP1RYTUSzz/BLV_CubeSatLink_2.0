# BLV Onboard Cutaway Mechanism Code
# Originally written by Michael Pham and Ali Malik
# Edited by Pragun Bethapudi and Vencionas Kosasih
# Most recent editor: Vencionas Kosasih

# import necessary libraries
import board
import busio
import digitalio
import time
import adafruit_rfm9x
from adafruit_motor import servo
import pwmio
import adafruit_gps 

pwm = pwmio.PWMOut(board.A0, frequency=50)
servo = servo.Servo(pwm, min_pulse=750, max_pulse=2250)

uart = busio.UART(board.TX, board.RX, baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)

gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")

# define variables to be used for the GPS values.
gps_alt = 0
gps_speed = 0
gps_track_angle = 0

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D10)
reset = digitalio.DigitalInOut(board.D11)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 437.4)

rfm9x.spreading_factor=8
rfm9x.tx_power=14
rfm9x.node=0xfb
rfm9x.destination=0xfa
rfm9x.receive_timeout=10
rfm9x.enable_crc=True
rfm9x.signal_bandwidth = 125000

servo.angle=180


# ====================================================================================================

# this defines "command keys," aka the two numbers at the end of
# the message required to actually execute a command.
cmd_keys = {
    b'65':   'cut_away',
    b'66':   'query',
    b'67':   'exec_cmd',
    b'68':   'ping',
    b'69':   'signal_status', # nice
    b'70':   'alt_status',
    b'71':   'coord_status'
}


# ====================================================================================================

# this defines a function that interprets the received message.

def cmd_handler(msg):
    try:
        header = msg[0:10]
        print(f"Re: {header}")

        # verify that the message is from us (unique string).
        # if not, it doesn't do anything (no "else" block).
        if msg[0:10] == b'KN6NAQ!CMD':
            print(f"CMD Received: {msg}")

            rfm9x.send("CMD ACK!")
            rfm9x.send("CMD ACK!")
            rfm9x.send("CMD ACK!")

            time.sleep(1)

            cmd_key = msg[10:12]
            print(f"Command key: {cmd_key}")

            #eval(cmd_keys[cmd_key]) <- not sure why this is here

            cmd_args = None
            cmd_args = msg[10:]
            print(f"CMD with ARGS: {cmd_args}")
            print(f"Character count: {len(msg)}")

            # this links a specific function to each specific message.
            # these functions are defined in a later section.
            if msg == "KN6NAQ!CMD65":
                cut_away()
            if msg == "KN6NAQ!CMD69":
                signal_status()
            if msg == "KN6NAQ!CMD70":
                alt_status()
            if msg == "KN6NAQ!CMD71":
                coord_status()


            if cmd_key in cmd_keys:
                try:
                    if cmd_args is None:
                        print('running {} (no args)'.format(cmd_keys[cmd_key]))
                        # eval a string turns it into a func name
                        eval(cmd_keys[cmd_key])()
                    else:
                        print('running {} (with args: {})'.format(cmd_keys[cmd_key],cmd_args))
                        eval(cmd_keys[cmd_key])#(cmd_args)

                except Exception as e:
                    print('Something went wrong: {}'.format(e))
                    rfm9x.send(str(e).encode())

            else:
                print('invalid command!')
                rfm9x.send(b'invalid cmd_key' + msg[11:])

    except Exception as e:
        print(e)


# ====================================================================================================

# this defines a function that handles all the gps info

def gps_handler(gps_alt, gps_speed, gps_track_angle):
    # Make sure to call gps.update() every loop iteration and at least twice
    # as fast as data comes from the GPS unit (usually every second).
    # This returns a bool that's true if it parsed new data (you can ignore it
    # though if you don't care and instead look at the has_fix property).
    gps.update()
    # Every second print out current location details if there's a fix.

    print("=" * 40)  # Print a separator line.

    if not gps.has_fix:
        # Try again if we don't have a fix yet.
        print("Waiting for fix...")

        return "No GPS Fix"
    # We have a fix! (gps.has_fix is true)
    # Print out details about the fix like location, date, etc.

    print(
        "Fix timestamp UTC: {}/{}/{} {:02}:{:02}:{:02}".format(
            gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
            gps.timestamp_utc.tm_mday,  # struct_time object that holds
            gps.timestamp_utc.tm_year,  # the fix time.  Note you might
            gps.timestamp_utc.tm_hour,  # not get all data like year, day,
            gps.timestamp_utc.tm_min,  # month!
            gps.timestamp_utc.tm_sec,
        )
    )
    print("Latitude: {0:.6f} degrees".format(gps.latitude))
    print("Longitude: {0:.6f} degrees".format(gps.longitude))

    print("Fix quality: {}".format(gps.fix_quality))
    # Some attributes beyond latitude, longitude and timestamp are optional
    # and might not be present.  Check if they're None before trying to use!
    if gps.altitude_m is not None:
        print("Altitude: {} meters".format(gps.altitude_m))
        gps_alt = gps.altitude_m
    if gps.speed_knots is not None:
        print("Speed: {} knots".format(gps.speed_knots))
        gps_speed = gps.speed_knots
    if gps.track_angle_deg is not None:
        print("Track angle: {} degrees".format(gps.track_angle_deg))
        gps_track_angle = gps.track_angle_deg

    gps_data_string = "UTC Time {}/{}/{} {:02}:{:02}:{:02} | Lat: {} Long: {} | Alt: {} | Knts: {} | TRKA: {}".format(
        gps.timestamp_utc.tm_mon,  # Grab parts of the time from the
        gps.timestamp_utc.tm_mday,  # struct_time object that holds
        gps.timestamp_utc.tm_year,  # the fix time.  Note you might
        gps.timestamp_utc.tm_hour,  # not get all data like year, day,
        gps.timestamp_utc.tm_min,  # month!
        gps.timestamp_utc.tm_sec,
        gps.latitude,
        gps.longitude,
        gps_alt,
        gps_speed,
        gps_track_angle
    )

    return gps_data_string


# ====================================================================================================

# this section defines functions that correspond to the "command keys"

def cut_away():
    print("Cutting!")
    servo.angle = 0
    rfm9x.send("Cut Away Initiated")

def ping():
    rfm9x.destination=0xff
    rfm9x.send(f"This is the Bronco Space BLV Callsign KN6NAQ! Time: {time.monotonic()}. Last RSSI: {rfm9x.last_rssi}")
    rfm9x.destination=0xfb

def query(args):
    print(f'query: {args}')
    print(rfm9x.send(data=str(eval(args))))

def exec_cmd(args):
    print(f'exec: {args}')
    exec(args)

def signal_status():
    print("Sending signal status and confirmation!")
    rfm9x.send("Packet received! Relaying RSSI.")

def alt_status():
    print("Sending current altitude!")
    if gps.has_fix:
        if gps.altitude_m is not None:
            rfm9x.send(f"Altitude: {gps.altitude_m} meters")
        else:
            rfm9x.send("GPS has a fix, but altitude not available! Please try again.")
    else:
        rfm9x.send("GPS does not have a fix! Please try again.")

def coord_status():
    print("Sending coordinates!")
    if gps.has_fix:
        rfm9x.send("""Latitude: {} degrees, Longitude: {} degrees""".format(round(gps.latitude, 6), round(gps.longitude,6)))
    else:
        rfm9x.send("GPS does not have a fix! Please try again.")


# ====================================================================================================

# this is the actual looping code (must define all functions beforehand)

while True:
    rfm9x.send(gps_handler(gps_alt, gps_speed, gps_track_angle))
    msg = rfm9x.receive()

    print(f"Message received: {msg} ; RSSI: {rfm9x.last_rssi}")

    if msg is not None:
        cmd_handler(msg)
        # cutaway manual activation OR signal status OR gps status
    if gps_alt == 31500:
        cut_away()
        # cutaway automatic activation

    time.sleep(1)
