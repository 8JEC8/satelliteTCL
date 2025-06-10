# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

from commander import Commander
from machine import SDCard, Timer
from peer_tcp import Peer
from sock import Socker
import micropython
import network_interface as ni
import os

micropython.alloc_emergency_exception_buf(100) # reserve memory for call back error stacks

nif = ni.Nif()
sd = SDCard(slot=2)
vfs = os.VfsFat(sd)
os.mount(vfs, "/sd") #Montar sd

nif.setup_sta()

socket = Socker()

Peer.DEFAULT_EXT_ID = 'sputnik'  # our identity
socket.peers["earth"] = Peer(('192.168.4.1', 8081), "earth", 0, None, outbound=True)

commands = Commander(socket)
commands.masters.append('earth')

tim = Timer(3)
tim.init(mode = Timer.PERIODIC, freq = 100, callback = commands._refresh)
