from commander import Commander
from peer_tcp import Peer
from sock import Socker

socket = Socker()

Peer.DEFAULT_EXT_ID = 'rodro'  # our identity
socket.peers["earth"] = Peer(('172.16.20.157', 8081), "earth", 0, None, outbound=True)

commands = Commander(socket)
commands.masters.append('earth')
commands._refresh()

