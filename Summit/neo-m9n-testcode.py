import time
import board
import busio

from neo_m9n_spi import (
    NeoM9nSPI,
    UBX_CLASS_NAV,
    UBX_ID_NAV_PVT,
    DYNMODEL_AIRBORNE_1G,
    dynamic_model_name,
)


# ============================================================
# WIRING
# ============================================================
#
# NEO-M9N    Pico 2 / RP2350
# ----------------------------
# VCC        3V3
# GND        GND
# SCK        GP18
# MOSI/SDI   GP19
# MISO/SDO   GP16
# CS/SS      GP17
#
# Use 3.3 V logic only.


# ============================================================
# SPI PINS
# ============================================================

SPI_SCK = board.GP14
SPI_MOSI = board.GP15
SPI_MISO = board.GP12
GPS_CS = board.GP13


# ============================================================
# CREATE SPI BUS
# ============================================================

spi = busio.SPI(
    clock=SPI_SCK,
    MOSI=SPI_MOSI,
    MISO=SPI_MISO,
)


# ============================================================
# CREATE GPS OBJECT
# ============================================================

gps = NeoM9nSPI(
    spi=spi,
    cs_pin=GPS_CS,
    baudrate=1_000_000,
)


# ============================================================
# STARTUP CONFIG
# ============================================================
#
# For a 100,000 ft high-altitude balloon, use Airborne <1g
# from startup. Do not wait until high altitude to switch.
#
# This setting is RAM-only. It is re-applied every boot.

print("NEO-M9N SPI high-altitude balloon reader started")

gps.set_dynamic_model_if_changed(DYNMODEL_AIRBORNE_1G)


def print_pvt(pvt):
    """
    Print position, altitude, and fix information.
    """

    print(
        "{} | mode={} | fix={} | ok={} | sats={} | lat={:.7f} | lon={:.7f} | altMSL={:.1f} m | altMSL={:.0f} ft | vAcc={:.1f} m | speed={:.2f} m/s".format(
            pvt["time_utc"],
            dynamic_model_name(gps.current_dynmodel),
            gps.fix_type_name(pvt["fix_type"]),
            pvt["gnss_fix_ok"],
            pvt["satellites"],
            pvt["latitude"],
            pvt["longitude"],
            pvt["height_msl_m"],
            pvt["height_msl_m"] * 3.28084,
            pvt["vertical_accuracy_m"],
            pvt["ground_speed_m_s"],
        )
    )


# ============================================================
# MAIN LOOP
# ============================================================

while True:
    # Ask GPS for one UBX-NAV-PVT packet.
    #
    # SPI does not let the GPS push data by itself.
    # The Pico must ask for data and clock bytes out.
    gps.poll_nav_pvt()

    # Give the GPS a short moment to prepare response bytes.
    time.sleep(0.15)

    # Read bytes over SPI and parse complete UBX packets.
    packets = gps.read_packets(read_size=768)

    for msg_class, msg_id, payload in packets:
        if msg_class == UBX_CLASS_NAV and msg_id == UBX_ID_NAV_PVT:
            pvt = gps.parse_nav_pvt(payload)

            if pvt is None:
                continue

            print_pvt(pvt)

    time.sleep(0.85)