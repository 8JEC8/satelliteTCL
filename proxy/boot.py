# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import network

# ap interface
ap_ssid = "Earth"
ap_password = "1q2w3e4r5t6y"

ap = network.WLAN(network.AP_IF)
ap.config(ssid=ap_ssid, password=ap_password)
ap.active(True)


# st interface for LAN access
st_ssid = "Candy_2.4G"
st_pwd = "Yh3!V6Y!2wfm"

st = network.WLAN(network.STA_IF)
st.active(False) # assert inactive on reboot
st.active(True)
st.connect(st_ssid, st_pwd)
