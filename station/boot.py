# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import micropython
import network_interface as ni
import led
import sock

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif()
nif.setup_sta()

socket = sock.Socker()
import peer_tcp
pi = peer_tcp.Peer(('192.168.4.1', 8081), "me", 0, None)
socket.peers["me"] = pi
