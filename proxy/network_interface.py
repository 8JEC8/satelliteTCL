import network
import machine
import led

# [N]etwork [i]nter[f]ace
class Nif:

    def wifirecover_(self, t):
        print('wifirecover')
        if self.st.status() == network.STAT_GOT_IP:
            t.deinit()
            self.wificheck()
            return

        if self.st.status() < 1000: # in error
            self.led.red()
            self.led.on()
            return

    def wificheck_(self, t): # running in [OK] state
        print('wificheck')
        if self.st.status() != network.STAT_GOT_IP:
            t.deinit() 
            self.wifirecover()
            self.led.off()
            return

        self.led.green()
        self.led.on()

    def wificheck(self):
        self.tim1.init(mode = machine.Timer.PERIODIC, freq = 0.25, callback = lambda a : self.wificheck_)

    def wifirecover(self):
        self.tim2.init(mode = machine.Timer.PERIODIC, freq = 2, callback = lambda b : self.wifirecover_)

    def __init__(self):
        self.ap_ssid = "Earth"
        self.ap_password = "1q2w3e4r5t6y"
        self.st_ssid = "Candy_2.4G"
        self.st_pwd = "Yh3!V6Y!2wfm"
        self.tim1 = machine.Timer(1)
        self.tim2 = machine.Timer(2)
        self.led = led.Led()

    def setup_ap(self):
        self.ap = network.WLAN(network.AP_IF)
        self.ap.config(ssid=self.ap_ssid, password=self.ap_password)
        self.ap.active(True)
        # is launched instantly

    def setup_st(self):
        self.st = network.WLAN(network.STA_IF)
        self.st.active(False) # assert inactive
        self.st.active(True)
        self.st.connect(self.st_ssid, self.st_pwd) 

        self.wificheck(self)
'''
Possible status codes for if.status()
    ASSOC FAIL - 203
    BEACON TIMEOUT - 200
    CONNECTING - 1001
    GOT IP - 1010
    HANDSHAKE TIMEOUT - 204
    IDLE - 1000
    NO AP FOUND - 201
    NO AP FOUND IN AUTHMODE TRESHOLD - 211
    NO AP FOUND IN RSSI TRESHOLD - 212
    NO AP FOUND W COMPATIBLE SECURITY - 210
    WRONG PASSWORD - 202
'''
