import time
import struct
import digitalio


# ============================================================
# UBX CONSTANTS
# ============================================================

UBX_SYNC_1 = 0xB5
UBX_SYNC_2 = 0x62

# UBX message classes / IDs
UBX_CLASS_NAV = 0x01
UBX_ID_NAV_PVT = 0x07

UBX_CLASS_ACK = 0x05
UBX_ID_ACK_NAK = 0x00
UBX_ID_ACK_ACK = 0x01

UBX_CLASS_CFG = 0x06
UBX_ID_CFG_VALSET = 0x8A

# u-blox M9 dynamic platform model config key
CFG_NAVSPG_DYNMODEL = 0x20110021

# Dynamic model values
DYNMODEL_PORTABLE = 0
DYNMODEL_STATIONARY = 2
DYNMODEL_PEDESTRIAN = 3
DYNMODEL_AUTOMOTIVE = 4
DYNMODEL_SEA = 5
DYNMODEL_AIRBORNE_1G = 6
DYNMODEL_AIRBORNE_2G = 7
DYNMODEL_AIRBORNE_4G = 8


def dynamic_model_name(model):
    if model == DYNMODEL_PORTABLE:
        return "Portable"
    if model == DYNMODEL_STATIONARY:
        return "Stationary"
    if model == DYNMODEL_PEDESTRIAN:
        return "Pedestrian"
    if model == DYNMODEL_AUTOMOTIVE:
        return "Automotive"
    if model == DYNMODEL_SEA:
        return "Sea"
    if model == DYNMODEL_AIRBORNE_1G:
        return "Airborne <1g"
    if model == DYNMODEL_AIRBORNE_2G:
        return "Airborne <2g"
    if model == DYNMODEL_AIRBORNE_4G:
        return "Airborne <4g"
    return "Unknown"


class NeoM9nSPI:
    """
    Simple u-blox NEO-M9N SPI driver for CircuitPython.

    Important SPI idea:
        SPI is controlled by the Pico.
        The GPS cannot send data whenever it wants.
        The Pico must send dummy bytes to create clock pulses.

    This driver:
        - sends UBX commands
        - reads raw SPI bytes
        - finds complete UBX packets
        - parses UBX-NAV-PVT
        - sets the dynamic platform model
    """

    def __init__(self, spi, cs_pin, baudrate=1_000_000):
        self.spi = spi
        self.baudrate = baudrate

        self.cs = digitalio.DigitalInOut(cs_pin)
        self.cs.direction = digitalio.Direction.OUTPUT
        self.cs.value = True

        # Buffer for raw bytes read from SPI.
        # UBX packets can be split across reads, so we keep leftovers here.
        self.buffer = b""

        self.current_dynmodel = None

        self.configure_spi()

    def configure_spi(self):
        """
        Configure SPI mode.

        u-blox SPI normally uses:
            polarity = 0
            phase    = 0
            mode     = 0
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
        Full-duplex SPI transfer.

        SPI sends and receives at the same time.
        If tx is 100 bytes long, rx will also be 100 bytes long.
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

    def read_raw(self, count=512):
        """
        Read raw bytes from the GPS.

        To read over SPI, we send dummy 0xFF bytes.
        The GPS sends data back during those clock pulses.

        Do NOT delete all 0xFF bytes here.
        0xFF can appear inside a real UBX packet.
        The packet parser will discard junk safely.
        """

        dummy = bytearray([0xFF] * count)
        return self.transfer(dummy)

    def ubx_checksum(self, data):
        """
        Calculate UBX checksum.

        Checksum is over:
            class, id, length, payload

        Checksum does not include:
            0xB5 0x62
        """

        ck_a = 0
        ck_b = 0

        for b in data:
            ck_a = (ck_a + b) & 0xFF
            ck_b = (ck_b + ck_a) & 0xFF

        return ck_a, ck_b

    def make_ubx_packet(self, msg_class, msg_id, payload=b""):
        """
        Build one complete UBX packet.
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
        Send one UBX packet to the GPS.
        """

        packet = self.make_ubx_packet(msg_class, msg_id, payload)
        self.transfer(packet)

    def poll_nav_pvt(self):
        """
        Ask the GPS for one UBX-NAV-PVT packet.

        NAV-PVT includes:
            fix type
            valid fix flag
            latitude
            longitude
            altitude
            speed
            heading
            satellite count
        """

        self.send_ubx(UBX_CLASS_NAV, UBX_ID_NAV_PVT)

    def parse_ubx_from_buffer(self):
        """
        Search self.buffer for complete UBX packets.

        Returns:
            list of (msg_class, msg_id, payload)

        Why this is needed:
            One SPI read might contain half a packet.
            The next SPI read might contain the rest.
        """

        packets = []

        while True:
            sync = bytes([UBX_SYNC_1, UBX_SYNC_2])
            start = self.buffer.find(sync)

            if start < 0:
                # Keep a trailing 0xB5 in case the next read starts with 0x62.
                if len(self.buffer) > 0 and self.buffer[-1] == UBX_SYNC_1:
                    self.buffer = self.buffer[-1:]
                else:
                    self.buffer = b""
                return packets

            # Discard junk before sync bytes.
            if start > 0:
                self.buffer = self.buffer[start:]

            # Need at least header + checksum.
            if len(self.buffer) < 8:
                return packets

            msg_class = self.buffer[2]
            msg_id = self.buffer[3]
            length = self.buffer[4] | (self.buffer[5] << 8)

            total_length = 6 + length + 2

            # Wait for more bytes if packet is incomplete.
            if len(self.buffer) < total_length:
                return packets

            packet = self.buffer[:total_length]
            payload = packet[6:6 + length]

            ck_a, ck_b = self.ubx_checksum(packet[2:6 + length])

            if ck_a == packet[-2] and ck_b == packet[-1]:
                packets.append((msg_class, msg_id, payload))

            # Remove parsed packet from buffer.
            self.buffer = self.buffer[total_length:]

    def read_packets(self, read_size=512):
        """
        Read from SPI and return any complete UBX packets found.
        """

        raw = self.read_raw(read_size)
        self.buffer += raw

        # Prevent unlimited growth if wiring/config is wrong.
        if len(self.buffer) > 4096:
            self.buffer = self.buffer[-512:]

        return self.parse_ubx_from_buffer()

    def parse_nav_pvt(self, payload):
        """
        Decode UBX-NAV-PVT.

        Payload length is normally 92 bytes.
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

        # height = above ellipsoid
        # height_msl = above mean sea level
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

    def set_dynamic_model(self, model, save_to_ram=True, save_to_bbr=False, save_to_flash=False):
        """
        Set dynamic platform model using UBX-CFG-VALSET.

        Recommended for flight code:
            save_to_ram=True
            save_to_bbr=False
            save_to_flash=False

        That means the config is applied now, but not permanently burned.
        """

        layers = 0

        if save_to_ram:
            layers |= 0x01

        if save_to_bbr:
            layers |= 0x02

        if save_to_flash:
            layers |= 0x04

        payload = bytearray()

        # VALSET header
        payload.append(0x00)      # version
        payload.append(layers)    # layers
        payload.append(0x00)      # reserved
        payload.append(0x00)      # reserved

        # Key ID: CFG-NAVSPG-DYNMODEL, little-endian
        payload.extend(struct.pack("<I", CFG_NAVSPG_DYNMODEL))

        # Value: one-byte enum
        payload.append(model)

        self.send_ubx(UBX_CLASS_CFG, UBX_ID_CFG_VALSET, payload)

        self.current_dynmodel = model

    def set_dynamic_model_if_changed(self, model):
        """
        Avoid repeatedly sending the same config command.
        """

        if self.current_dynmodel != model:
            print("Setting dynamic model:", dynamic_model_name(model))
            self.set_dynamic_model(model)
            time.sleep(0.2)