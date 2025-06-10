import network
import machine
import led
import ntptime
import json
import logger as logs

log = logs.Logger('WiFi')


class Nif:
    sta = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    def wifirecover_(self, t):
        if Nif.sta.status() == network.STAT_GOT_IP:
            t.deinit()
            self.led.green()
            self.led.on()
            self.wificheck()
            if self.wanAccess and not self.timeSync:
                ntptime.settime()
                self.timeSync = True  # handle exception
            log.info("Connection recovered.")
            return

        if Nif.sta.status() < 1000:
            self.led.red()
            self.led.toggle()
            # return
        else:
            self.led.amber()
            self.led.toggle()

    def wificheck_(self, t):
        if Nif.sta.status() != network.STAT_GOT_IP:
            t.deinit()
            self.wifirecover()
            log.info("Connection lost.")
            return

    def wificheck(self):
        self.tim1.init(
                       mode=machine.Timer.PERIODIC,
                       freq=0.5,
                       callback=self.wificheck_)

    def wifirecover(self):
        self.tim1.init(
                       mode=machine.Timer.PERIODIC,
                       freq=2,
                       callback=self.wifirecover_)

    def __init__(self, wanAccess=False):
        self.keys = json.load(open('keys.json'))
        self.tim1 = machine.Timer(1)
        self.led = led.Led()
        self.wanAccess = wanAccess
        self.timeSync = False

    def setup_ap(self):
        Nif.ap.active(True)
        Nif.ap.config(
                       essid=self.keys['ap']['ssid'],
                       password=self.keys['ap']['key'],
                       security=3 if len(self.keys['ap']['key']) >= 8 else 0)

    def setup_sta(self):
        Nif.sta.active(False)  # assert inactive
        Nif.sta.active(True)
        Nif.sta.connect(
            self.keys['station']['ssid'],
            self.keys['station']['key'])
        self.wifirecover()


'''
docs.micropython.org/en/v1.24.0/library/network.WLAN.html
    BEACON TIMEOUT - 200
    NO AP FOUND - 201
    WRONG PASSWORD - 202
    ASSOC FAIL - 203
    HANDSHAKE TIMEOUT - 204
    NO AP FOUND W COMPATIBLE SECURITY - 210
    NO AP FOUND IN AUTHMODE TRESHOLD - 211
    NO AP FOUND IN RSSI TRESHOLD - 212
    IDLE - 1000
    CONNECTING - 1001
    GOT IP - 1010
'''
