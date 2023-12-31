import logging
import time
from dataclasses import dataclass
from enum import unique, Enum

import serial

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class Keycode:
    number: int
    hex: int


@unique
class KeyDefinitions(Keycode, Enum):
    # Special keys
    SPACE = 32, 0x2C
    SHIFT = 16, 0xe1
    CONTROL = 17, 0xe0
    ENTER = 13, 0x28
    BACKSPACE = 8, 0x2A
    ALT = 18, 0xE2
    TAB = 9, 0x2B
    ESCAPE = 27, 0x29
    WIN = 91, 0xE3
    CAPS_LOCK = 20, 0x39
    INSERT = 45, 0x49
    DELETE = 46, 0x4C
    PRINT_SCREEN = 44, 0x46
    SCROLL_LOCK = 145, 0x47
    Pause = 19, 0x48
    HOME = 36, 0x4A
    END = 35, 0x4D
    PAGE_UP = 33, 0x4B
    PAGE_DOWN = 34, 0x4E
    UP = 38, 0x52
    DOWN = 40, 0x51
    LEFT = 37, 0x50
    RIGHT = 39, 0x4F
    F1 = 112, 0x3A
    F2 = 113, 0x3B
    F3 = 114, 0x3C
    F4 = 115, 0x3D
    F5 = 116, 0x3E
    F6 = 117, 0x3F
    F7 = 118, 0x40
    F8 = 119, 0x41
    F9 = 120, 0x42
    F10 = 121, 0x43
    F11 = 122, 0x44
    F12 = 123, 0x45

    # Number (0-9)
    _0 = 48, 0x27
    _1 = 49, 0x1E
    _2 = 50, 0x1F
    _3 = 51, 0x20
    _4 = 52, 0x21
    _5 = 53, 0x22
    _6 = 54, 0x23
    _7 = 55, 0x24
    _8 = 56, 0x25
    _9 = 57, 0x26

    # upper case letter (A-Z)
    A = 65, 0x04
    B = 66, 0x05
    C = 67, 0x06
    D = 68, 0x07
    E = 69, 0x08
    F = 70, 0x09
    G = 71, 0x0A
    H = 72, 0x0B
    I = 73, 0x0C
    J = 74, 0x0D
    K = 75, 0x0E
    L = 76, 0x0F
    M = 77, 0x10
    N = 78, 0x11
    O = 79, 0x12
    P = 80, 0x13
    Q = 81, 0x14
    R = 82, 0x15
    S = 83, 0x16
    T = 84, 0x17
    U = 85, 0x18
    V = 86, 0x19
    W = 87, 0x1A
    X = 88, 0x1B
    Y = 89, 0x1C
    Z = 90, 0x1D

    # symbol keys
    MINUS = 189, 0x2D
    EQUAL = 187, 0x2E
    BRACKET_L = 219, 0x2F
    BRACKET_R = 221, 0x30
    BACKSLASH = 220, 0x31
    SEMICOLON = 186, 0x33
    APOSTROPHE = 222, 0x34
    GRAVE = 192, 0x35
    COMMA = 188, 0x36
    PERIOD = 190, 0x37
    SLASH = 191, 0x38

    # extra keys
    BLANK = 0, 0x00

    @classmethod
    def get_key(cls, keycode):
        for cl in cls:
            if cl.value.number == keycode:
                return cl
        return None


class CH9329:
    PRESSED_SHIFT = False
    PRESSED_CTRL = False
    PRESSED_ALT = False
    PRESSED_WIN = False

    def __init__(self, port="COM4", baud=9600):
        self.port = port  # open COM port
        self.baud = baud  # Baudrate
        self.ser = serial.Serial()
        self.ser.port = self.port
        self.ser.baudrate = self.baud
        self.ser.timeout = 0

        logger.debug(f"Open port: {self.port}, baud: {self.baud}")
        self.ser.open()

    def send_packet(self, data):
        debug_text = 'send [ '
        for i in data:
            debug_text += "{:02X}".format(i) + ' '
        debug_text += ']'
        logger.debug(debug_text)

        self.ser.write(bytes(data))
        time.sleep(0.02)
        return self.ser.read(7)

    def push(self, k0, k1, k2=0, k3=0, k4=0, k5=0, k6=0):
        # print(self.port,": ",hex(k0),hex(k1))
        packet_1 = [
            0x57, 0xAB,  # header (2byte)
            0x00,  # address (1byte)
            0x02,  # command (1byte)
            0x08,  # length (1byte)
            k0, 0x00, k1, k2, k3, k4, k5, k6,  # data (8byte)
        ]
        packet_1.append(sum(packet_1) & 0xff)  # checksum (1byte)
        self.send_packet(packet_1)

        packet_2 = [0x57, 0xAB, 0x00, 0x02, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c]
        self.send_packet(packet_2)

    def _build_modifier_byte(self):
        modifier_byte = 0x00
        if self.PRESSED_SHIFT:
            modifier_byte |= 0x02
        if self.PRESSED_CTRL:
            modifier_byte |= 0x01
        if self.PRESSED_ALT:
            modifier_byte |= 0x04
        if self.PRESSED_WIN:
            modifier_byte |= 0x08
        return modifier_byte

    def key_press(self, keycode):
        key = KeyDefinitions.get_key(keycode)
        if key == KeyDefinitions.SHIFT:
            self.PRESSED_SHIFT = True
            key = KeyDefinitions.BLANK
        elif key == KeyDefinitions.CONTROL:
            self.PRESSED_CTRL = True
            key = KeyDefinitions.BLANK
        elif key == KeyDefinitions.ALT:
            self.PRESSED_ALT = True
            key = KeyDefinitions.BLANK
        elif key == KeyDefinitions.WIN:
            self.PRESSED_WIN = True
            key = KeyDefinitions.BLANK
        else:
            pass

        if key:
            logger.debug(
                f"press {keycode} SHIFT:{self.PRESSED_SHIFT} CTRL:{self.PRESSED_CTRL} ALT:{self.PRESSED_ALT} WIN:{self.PRESSED_WIN}")
            self.push(self._build_modifier_byte(), key.hex)
        else:
            logger.error("Not found key code", keycode)

    def key_release(self, keycode):
        key = KeyDefinitions.get_key(keycode)
        if key == KeyDefinitions.SHIFT:
            self.PRESSED_SHIFT = False
        elif key == KeyDefinitions.CONTROL:
            self.PRESSED_CTRL = False
        elif key == KeyDefinitions.ALT:
            self.PRESSED_ALT = False
        elif key == KeyDefinitions.WIN:
            self.PRESSED_WIN = False
        else:
            pass

        logger.debug(
            f"release {keycode} SHIFT:{self.PRESSED_SHIFT} CTRL:{self.PRESSED_CTRL} ALT:{self.PRESSED_ALT} WIN:{self.PRESSED_WIN}")

    def close(self):
        if self.ser.isOpen():
            self.ser.close()

    def __del__(self):
        self.close()
