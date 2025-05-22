# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

from commander import Commander
from peer_tcp import Peer
import micropython
import network_interface as ni
import sock

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif(wanAccess=True)
nif.setup_sta()
nif.setup_ap()

Peer.DEFAULT_EXT_ID = 'earth'
socket = sock.Socker(serverPort=8081)
commands = Commander(socket)
commands.masters.append('sputnik')
