import network
import machine
import led

# [N]etwork [i]nter[f]ace
class Nif:

    def wifirecover_(self, t):
        if self.sta.status() == network.STAT_GOT_IP:
            t.deinit()
            self.led.green()
            self.led.on()
            self.wificheck()
            return

        if self.sta.status() < 1000:
            self.led.red()
            self.led.toggle()
            #return
        else:
            self.led.amber()
            self.led.toggle()

    def wificheck_(self, t):
        if self.sta.status() != network.STAT_GOT_IP:
            t.deinit() 
            self.wifirecover()
            return

    def wificheck(self):
        self.tim1.init(mode = machine.Timer.PERIODIC, freq = 0.5, callback = self.wificheck_)

    def wifirecover(self):
        self.tim1.init(mode = machine.Timer.PERIODIC, freq = 2, callback = self.wifirecover_)

    def __init__(self):
        self.tim1 = machine.Timer(1)
        self.led = led.Led()
        self.ap = network.WLAN(network.AP_IF)
        self.sta = network.WLAN(network.STA_IF)

    def setup_ap(self):
        self.ap.active(True)

    def setup_sta(self, ssid, pwd):
        self.sta.active(False) # assert inactive
        self.sta.active(True)
        self.sta.connect(ssid, pwd) 
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
