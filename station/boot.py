# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

from commander import Commander
from peer_tcp import Peer
from sock import Socker
import micropython
import network_interface as ni
import led

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif()
nif.setup_sta()

socket = Socker()

Peer.DEFAULT_EXT_ID = 'sputnik'  # our identity
socket.peers["earth"] = Peer(('192.168.4.1', 8081), "earth", 0, None, outbound=True)

commands = Commander(socket)
commands.masters.append('earth')
