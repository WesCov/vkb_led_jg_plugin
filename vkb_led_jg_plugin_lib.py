"""

vkb_led_jg_plugin_lib.py

LEDClass, get_LED_configs, set_LEDs, and _LED_conf_checksum are from the pyvkb package by
ventorvar.  Modifications are limiting RGB values to 0 to 7, open and closing the VKB device,
and adding a dummy LED the set process to get around a read error. 

The following is from ventorvar:
    
Setting the LEDs consists of a possible 30 LED configs each of which is a 4 byte structure as follows:

byte 0:  LED ID
bytes 2-4: a 24 bit color config as follows::

    000 001 010 011 100 101 110 111
    clm lem  b2  g2  r2  b1  g1  r1

color mode (clm):
    0 - color1
    1 - color2
    2 - color1/2
    3 - color2/1
    4 - color1+2

led mode (lem):
    0 - off
    1 - constant
    2 - slow blink
    3 - fast blink
    4 - ultra fast

Colors:
    VKB uses a simple RGB color configuration for all LEDs. Non-rgb LEDs will not light if you set their primary
    color to 0 in the color config. The LEDs have a very reduced color range due to VKB using 0-7 to determine the
    brightness of R, G, and B.
"""

"""
    The remaining functions are utilities to translate UI input or search the USB Lighting report
"""


import os
import pywinusb.hid as hid

import struct
import bitstruct as bs

LED_REPORT_ID = 0x59
LED_REPORT_LEN = 129
LED_SET_OP_CODE = bytes.fromhex("59a50a")
LED_CONFIG_COUNT = 4    # plus a dummy


class LEDClass:
    def __init__(self,
                 LED_id = 0,
                 colorMode = 0,
                 LEDMode = 0,
                 color1 = [0, 0, 0],
                 color2 = [0, 0, 0]):

        self.LED_id = int(LED_id)
        self.colorMode = colorMode
        self.LEDMode = LEDMode
        self.color1 = color1
        self.color2 = color2

    def __repr__(self):
        return (f"<LED_id:{self.LED_id} colorMode:{self.colorMode} LEDMode:{self.LEDMode} "
                f"color1:{self.color1} color2:{self.color2}>")

    def __bytes__(self):
        return struct.pack(">B", self.LED_id) + bs.byteswap("3",
                                                            bs.pack("u3" * 8,
                                                                    self.colorMode,
                                                                    self.LEDMode,
                                                                    *self.color2[::-1],
                                                                    *self.color1[::-1],),)
    
    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, LEDClass):
            return NotImplemented
        return (self.LED_id == other.LED_id and
                self.colorMode == other.colorMode and
                self.LEDMode == other.LEDMode and
                self.color1[0] == other.color1[0] and
                self.color1[1] == other.color1[1] and
                self.color1[2] == other.color1[2] and
                self.color2[0] == other.color2[0] and
                self.color2[1] == other.color2[1] and
                self.color2[2] == other.color2[2])

    def __ne__(self, other):
        return not self.__eq__(other)


    @classmethod
    def unpack(cls, buf):
        assert len(buf) == 4
        LED_id = int(buf[0])
        buf = bs.byteswap("3", buf[1:])
        colorMode, LEDMode, b2, g2, r2, b1, g1, r1 = bs.unpack("u3" * 8, buf)
        return cls(LED_id=LED_id,
                   colorMode=colorMode,
                   LEDMode=LEDMode,
                   color1=[r1, g1, b1],
                   color2=[r2, g2, b2])
'''
   There is an error when reading the last LED of the usage report: the led_mode field is
   always 0 regardless of original setting.  I cannot figure out how to fix it so I am
   getting around the probllem by always adding a dummy lED at the end of the list
   when setting the LEDs and not pulling it from LED report.
'''

def get_LED_configs(dev):
    dev.open()
    LED_report = [_ for _ in dev.find_feature_reports() if _.report_id == LED_REPORT_ID][0]
    data = bytes(LED_report.get(False))
    dev.close()
    assert len(data) >= 8
    if data[:3] != LED_SET_OP_CODE:
        return ([])  # it wont be returned until something is set, so default to showing no configs
    num_LED_configs = int(data[7])
    data = data[8:]
    LEDs = []
    for i in range(num_LED_configs - 1):
        LEDs.append(LEDClass.unpack(data[:4]))
        data = data[4:]
    return LEDs

def set_LEDs(dev, LED_configs):
    LED_configs.append(LEDClass(LED_id=99))
    num_configs = len(LED_configs)
    if num_configs > LED_CONFIG_COUNT:
        raise ValueError(f"Can only set a maximum of {LED_CONFIG_COUNT} LED configs")
    LED_configs = b"".join(bytes(_) for _ in LED_configs)
    LED_configs = os.urandom(2) + struct.pack(">B", num_configs) + LED_configs
    chksum = _LED_conf_checksum(num_configs, LED_configs)
    cmd = LED_SET_OP_CODE + chksum + LED_configs
    cmd = cmd + b"\x00" * (LED_REPORT_LEN - len(cmd))
    dev.open()
    LED_report = [_ for _ in dev.find_feature_reports() if _.report_id == LED_REPORT_ID][0]
    LED_report.send(cmd)
    dev.close()


def _LED_conf_checksum(num_configs, buf):
    
    def conf_checksum_bit(chk, b):
        chk ^= b
        for i in range(8):
            _ = chk & 1
            chk >>= 1
            if _ != 0:
                chk ^= 0xA001
        return chk

    chk = 0xFFFF
    for i in range((num_configs + 1) * 3):
        chk = conf_checksum_bit(chk, buf[i])
    return struct.pack("<H", chk)


'''
code specifc to vkb_led_jg_plugin

'''

class controlStateClass:
    
    def __init__(self,
                 vkbDevice = None,
                 LED_id = None,
                 LEDConfig = None,
                 defaultLED = None,
                 priorLED = None,
                 buttonStateOn = False,
                 whilePressed = False):
        
        self.vkbDevice = vkbDevice
        self.LED_id = LED_id
        self.LEDConfig = LEDConfig
        self.defaultLED = defaultLED
        self.priorLED = priorLED
        self.buttonStateOn = buttonStateOn
        self.whilePressed = whilePressed


def LEDNameToId(s):
    if s.upper() == "BASE":
        return 0
    elif s.upper() == "HAT":
        return 11
    elif s.upper() == "RGB":
        return 10
    else:
        return None

def stringRGBToList(s):
    result = (0,0,0)
    if len(s) == 5 and s.count(',') == 2:
        if (0 <= int(s[0]) <= 7) and (0 <= int(s[2]) <= 7) and (0 <= int(s[4]) <= 7):
            result = (int(s[0]), int(s[2]), int(s[4]))
    return result


def getUSBDevice(vendor_id, product_id):
    theDevice = hid.HidDeviceFilter(vendor_id=vendor_id, product_id=product_id).get_devices()
    if len(theDevice)==0:
        return None
    else:
        return theDevice[0] 

# search the USB lighting report results for a specific LED
def getLEDIndex(LED_id, LEDConfigs):
    i=0
    while i < len(LEDConfigs) and LEDConfigs[i].LED_id != LED_id:
        i+=1
    if i == len(LEDConfigs):
        return None
    else:
        return i
