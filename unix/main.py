from commander import Commander
from peer_tcp import Peer
from sock import Socker
from logger import Logger

socket = Socker()
commands = Commander(socket)
commands._refresh()

Peer.DEFAULT_EXT_ID = 'rodro'  # our identity

def setExtId(id):
    Peer.DEFAULT_EXT_ID = id

def connectTo(refName, host, port): # string, string, int
    socket.peers[refName] = Peer((host, port), refName, 0, None, outbound=True)
    commands.masters.append(refName)

def setPrinter(func):
    print(f'Reassigning printer to {func}')
    Logger.Printer = func

def getPhysicalStatus():
    #return ((25, 80), (3.3, 77), (13.2, 13.3, 13.4), (-10,))
    return commands.readStatus()
    # (temp/hum), (volt, mAmp), (xdeg, ydeg, zdeg), (rssi)
