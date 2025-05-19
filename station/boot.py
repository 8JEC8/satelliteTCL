# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

from peer_tcp import Peer
from sock import Socker
import micropython
import network_interface as ni
import led

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif()
nif.setup_sta()

socket = Socker()
pi = Peer(('192.168.4.1', 8081), "me", 0, None, outbound=True)
socket.peers["me"] = pi
pi2 = Peer(('192.168.4.1', 8081), "johnson", 0, None, outbound=True)
socket.peers["johnson"] = pi2
