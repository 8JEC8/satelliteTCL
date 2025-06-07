#import machine, neopixel

class Led:
    def __init__(self):
        self.color = [0, 0, 0]
        self.active = False
        #self.led = neopixel.NeoPixel(machine.Pin(38), 1)
        #self.led[0] = self.color
        #self.led.write()
        
    def on(self):
        self.active = True
        #self.led[0] = self.color
        #self.led.write()

    def off(self):
        self.active = False
        #self.led[0] = [0, 0 ,0]
        #self.led.write()
    
    def red(self):
        #self.color = [2, 0, 0]
        pass

    def green(self):
        #self.color = [0, 2, 0]
        pass

    def amber(self):
        #self.color = [2, 1, 0]
        pass

    def toggle(self):
        if self.active:
            self.off()
        else:
            self.on()
