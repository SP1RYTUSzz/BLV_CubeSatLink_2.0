import time
import struct
import digitalio


# ============================================================
# UBX CONSTANTS
# ============================================================

UBX_SYNC_1 = 0xB5
UBX_SYNC_2 = 0x62

# UBX-NAV-PVT
UBX_CLASS_NAV = 0x01
UBX_ID_NAV_PVT = 0x07

# UBX-CFG-VALSET
UBX_CLASS_CFG = 0x06
UBX_ID_CFG_VALSET = 0x8A

# Configuration key for dynamic platform model on u-blox M9
CFG_NAVSPG_DYNMODEL = 0x20110021

# Dynamic model values
DYNMODEL_PORTABLE = 0
DYNMODEL_AIRBORNE_1G = 6
DYNMODEL_AIRBORNE_2G = 7
DYNMODEL_AIRBORNE_4G = 8


def dynamic_model_name(model):
    if model == DYNMODEL_PORTABLE:
        return "Portable"
    if model == DYNMODEL_AIRBORNE_1G:
        return "Airborne <1g"
    if model == DYNMODEL_AIRBORNE_2G:
        return "Airborne <2g"
    if model == DYNMODEL_AIRBORNE_4G:
        return "Airborne <4g"
    return "Unknown"


class NeoM9nSPI:
    """
    Simple NEO-M9N SPI driver for CircuitPython.

    SPI is master-controlled. That means the Pico must send dummy
    bytes to create clock pulses before the GPS can return data.
    """

    def __init__(self, spi, cs_pin, baudrate=1_000_000):
        self.spi = spi
        self.baudrate = baudrate

        self.cs = digitalio.DigitalInOut(cs_pin)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.cs.value = True

        # Keeps partial UBX packets between reads.
        self.buffer = b""

        self.current_dynmodel = None

        self.configure_spi()

    def configure_spi(self):
        """
        Configure SPI mode 0.
        """

        while not self.spi.try_lock():
            pass

        try:
            self.spi.configure(
                baudrate=self.baudrate,
                polarity=0,
                phase=0,
                bits=8,
            )
        finally:
            self.spi.unlock()

    def transfer(self, tx):
        """
        Send bytes and receive bytes at the same time.

        SPI is full-duplex:
            every transmitted byte also receives one byte.
        """

        rx = bytearray(len(tx))

        while not self.spi.try_lock():
            pass

        try:
            self.cs.value = False
            self.spi.write_readinto(tx, rx)
            self.cs.value = True
        finally:
            self.spi.unlock()

        return bytes(rx)

    def read_raw(self, count=768):
        """
        Read raw bytes from the GPS.

        To read using SPI, we send dummy 0xFF bytes.
        The GPS sends data back during those clock pulses.

        Important:
            Do not remove all 0xFF bytes here.
            0xFF can appear inside a valid UBX packet.
        """

        dummy = bytearray([0xFF] * count)
        return self.transfer(dummy)

    def ubx_checksum(self, data):
        """
        Calculate UBX checksum.

        Checksum is calculated over:
            class, id, length, payload

        It does not include the 0xB5 0x62 sync bytes.
        """

        ck_a = 0
        ck_b = 0

        for b in data:
            ck_a = (ck_a + b) & 0xFF
            ck_b = (ck_b + ck_a) & 0xFF

        return ck_a, ck_b

    def make_ubx_packet(self, msg_class, msg_id, payload=b""):
        """
        Build a complete UBX packet.
        """

        length = len(payload)

        packet = bytearray()
        packet.append(UBX_SYNC_1)
        packet.append(UBX_SYNC_2)
        packet.append(msg_class)
        packet.append(msg_id)
        packet.append(length & 0xFF)
        packet.append((length >> 8) & 0xFF)
        packet.extend(payload)

        ck_a, ck_b = self.ubx_checksum(packet[2:])
        packet.append(ck_a)
        packet.append(ck_b)

        return packet

    def send_ubx(self, msg_class, msg_id, payload=b""):
        """
        Send a UBX command packet to the GPS.
        """

        packet = self.make_ubx_packet(msg_class, msg_id, payload)
        self.transfer(packet)

    def poll_nav_pvt(self):
        """
        Request one UBX-NAV-PVT message.

        NAV-PVT contains:
            time
            fix type
            valid fix flag
            latitude
            longitude
            altitude
            satellite count
            speed
            heading
        """

        self.send_ubx(UBX_CLASS_NAV, UBX_ID_NAV_PVT)

    def parse_ubx_from_buffer(self):
        """
        Search the byte buffer for complete UBX packets.

        Returns:
            list of (msg_class, msg_id, payload)
        """

        packets = []

        while True:
            sync = bytes([UBX_SYNC_1, UBX_SYNC_2])
            start = self.buffer.find(sync)

            if start < 0:
                # Keep a trailing 0xB5 in case next read starts with 0x62.
                if len(self.buffer) > 0 and self.buffer[-1] == UBX_SYNC_1:
                    self.buffer = self.buffer[-1:]
                else:
                    self.buffer = b""
                return packets

            # Remove junk before the sync bytes.
            if start > 0:
                self.buffer = self.buffer[start:]

            # Minimum UBX packet:
            # 2 sync + 1 class + 1 id + 2 length + 2 checksum = 8 bytes
            if len(self.buffer) < 8:
                return packets

            msg_class = self.buffer[2]
            msg_id = self.buffer[3]
            length = self.buffer[4] | (self.buffer[5] << 8)

            total_length = 6 + length + 2

            # Packet is incomplete; wait for more bytes.
            if len(self.buffer) < total_length:
                return packets

            packet = self.buffer[:total_length]
            payload = packet[6:6 + length]

            ck_a, ck_b = self.ubx_checksum(packet[2:6 + length])

            if ck_a == packet[-2] and ck_b == packet[-1]:
                packets.append((msg_class, msg_id, payload))

            # Remove this packet and continue searching.
            self.buffer = self.buffer[total_length:]

    def read_packets(self, read_size=768):
        """
        Read SPI bytes and return complete UBX packets.
        """

        raw = self.read_raw(read_size)
        self.buffer += raw

        # Prevent runaway memory growth if wiring or config is wrong.
        if len(self.buffer) > 4096:
            self.buffer = self.buffer[-512:]

        return self.parse_ubx_from_buffer()

    def parse_nav_pvt(self, payload):
        """
        Decode UBX-NAV-PVT.

        Payload is normally 92 bytes.
        """

        if len(payload) < 92:
            return None

        year = struct.unpack_from("<H", payload, 4)[0]
        month = payload[6]
        day = payload[7]
        hour = payload[8]
        minute = payload[9]
        second = payload[10]

        fix_type = payload[20]

        flags = payload[21]
        gnss_fix_ok = bool(flags & 0x01)

        satellites = payload[23]

        longitude = struct.unpack_from("<i", payload, 24)[0] / 10_000_000
        latitude = struct.unpack_from("<i", payload, 28)[0] / 10_000_000

        # height_m is above ellipsoid.
        # height_msl_m is above mean sea level.
        height_m = struct.unpack_from("<i", payload, 32)[0] / 1000
        height_msl_m = struct.unpack_from("<i", payload, 36)[0] / 1000

        horizontal_accuracy_m = struct.unpack_from("<I", payload, 40)[0] / 1000
        vertical_accuracy_m = struct.unpack_from("<I", payload, 44)[0] / 1000

        ground_speed_m_s = struct.unpack_from("<i", payload, 60)[0] / 1000
        heading_deg = struct.unpack_from("<i", payload, 64)[0] / 100_000

        return {
            "time_utc": "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                year, month, day, hour, minute, second
            ),
            "fix_type": fix_type,
            "gnss_fix_ok": gnss_fix_ok,
            "satellites": satellites,
            "latitude": latitude,
            "longitude": longitude,
            "height_m": height_m,
            "height_msl_m": height_msl_m,
            "horizontal_accuracy_m": horizontal_accuracy_m,
            "vertical_accuracy_m": vertical_accuracy_m,
            "ground_speed_m_s": ground_speed_m_s,
            "heading_deg": heading_deg,
        }

    def fix_type_name(self, fix_type):
        if fix_type == 0:
            return "no fix"
        if fix_type == 1:
            return "dead reckoning only"
        if fix_type == 2:
            return "2D fix"
        if fix_type == 3:
            return "3D fix"
        if fix_type == 4:
            return "GNSS + dead reckoning"
        if fix_type == 5:
            return "time-only fix"
        return "unknown"

    def set_dynamic_model(self, model):
        """
        Set the dynamic platform model using UBX-CFG-VALSET.

        This writes to RAM only.
        That means the setting is applied now, but not permanently saved.

        For a high-altitude balloon, use:
            DYNMODEL_AIRBORNE_1G
        """

        payload = bytearray()

        # UBX-CFG-VALSET header
        payload.append(0x00)  # version
        payload.append(0x01)  # layer: RAM only
        payload.append(0x00)  # reserved
        payload.append(0x00)  # reserved

        # Key ID, little-endian
        payload.extend(struct.pack("<I", CFG_NAVSPG_DYNMODEL))

        # Value, one byte
        payload.append(model)

        self.send_ubx(UBX_CLASS_CFG, UBX_ID_CFG_VALSET, payload)

        self.current_dynmodel = model

    def set_dynamic_model_if_changed(self, model):
        """
        Set dynamic model only if it changed.
        """

        if self.current_dynmodel != model:
            print("Setting dynamic model:", dynamic_model_name(model))
            self.set_dynamic_model(model)
            time.sleep(0.2)