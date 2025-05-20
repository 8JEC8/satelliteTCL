import sock
from peer_tcp import Peer
from commander import Commander


host = ('10.22.246.14', 8081)

socket = sock.Socker()
socket.peers['voltajo'] = Peer(host, 'voltajo', 0, None, outbound=True).setNetname('neurona')

commands = Commander(socket)
commands.masters.append('voltajo')
