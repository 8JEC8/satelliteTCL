# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import micropython
import network_interface as ni
import led

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif()
nif.setup_sta()
#nif.setup_ap()
