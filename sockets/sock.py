from bidict import BiMap
from logger import Logger
from peer_tcp import Peer
import machine
import socket
import select


# TODO: Enums, peerlist class, sequential acks
# Non-blocking inbound/outbound socket handler
class Socker:
    def __init__(self, serverPort=None):
        self.log = Logger('TCP-Sock', 'sockets.log')
        self.peers = {}
        self.nameToFd = BiMap()
        self.anons = {}

        self.server = None

        self.connector = select.poll()
        self.poller = select.poll()

        if serverPort:
            self.log.info('Enabling socket server.')
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', serverPort))
            self.server.listen(1)
            self.server.setblocking(False)
            self.log.debug(f'Socket server bound to 0.0.0.0:{serverPort}.')

            self.connector.register(self.server)

        self.log.info('Enabling peer handler.')

        # auto-updater
        self.tim2 = machine.Timer(2)
        self.tim2.init(mode=machine.Timer.PERIODIC, freq=5, callback=self._refresh)

    def _refresh(self, t):
        if self.server:
            waiting = self.connector.poll(1)
            if waiting and waiting[0][1] & select.POLLIN:
                client, address = waiting[0][0].accept()
                client.setblocking(False)
                self.log.info(f'Socket request accepted for {address}.')

                self.anons[client.fileno()] = Peer(None, "anon", Peer.ANON, client)
                self.poller.register(client)

        self.refreshOutbound()
        self.poll()

    def refreshOutbound(self):
        for peer in self.peers.values():
            if peer.outbound:
                if peer.status != Peer.GOOD and not self.connect_ex(peer):
                    peer.reset()
                    self.log.debug(f'Socket reset for peer "{peer.id}".')
                    # Unpolling/closing not necessary as it has been done by self.poll(), or never was polled/opened

    def connect_ex(self, peer):
        if peer.canConnect():
            self.log.debug(f'Connection attempt initiated to peer "{peer.id}".')
            try:
                peer.socket.connect(peer.host)
            except OSError as ex:
                peer.status = ex.errno
                self.log.debug(f'Connection attempt to peer "{peer.id}" status: {peer.status}.')
        elif not peer.isFailed():
            peer.status = Peer.GOOD
            peer.addAuth()
            self.poller.register(peer.socket)
            self.nameToFd.put(peer.id, peer.socket.fileno())
            self.log.info(f'Connected to peer "{peer.id}".')
        else:
            self.log.debug(f'Connection attempt failed to peer "{peer.id}": {peer.status}.')
            return False
        return True

    def closeSocket(self, peer):
        fileNo = peer.socket.fileno()
        try:
            peer.socket.close()
        except:
            self.log.warn(f'An exception occurred while closing socket for peer {peer.id}.')
            pass
        self.log.info(f'Connection closed for {peer.id}.')
        self.log.debug(f'Connection removal from poller')

        if peer.waitingAuth:
            del self.anons[fileNo]
            return

        if not peer.outbound:
            del self.peers[peer.id]
        else:
            peer.reset()

        self.nameToFd.delByKey(peer.id)  # Remove old fd reference

    def shutdown(self):
        self.tim2.deinit()
        self.log.info('Socket service shut down.')

    def poll(self):
        for s in self.poller.ipoll(1):
            if self.nameToFd.hasVal(s[0].fileno()):
                peer = self.peers[self.nameToFd.reverse[s[0].fileno()]]
            elif s[0].fileno() == -1:
                self.poller.unregister(s[0])
                return
            else:
                peer = self.anons[s[0].fileno()]

            if s[1] & select.POLLHUP or s[1] & select.POLLERR:  # close socket and clear its references
                self.closeSocket(peer)
                self.log.error(f'Socket closed from errored state for "{peer.id}".')
            if s[1] & select.POLLIN:
                self.saveInbuff(peer)
            if s[1] & select.POLLOUT:
                self.flushOutbuff(peer)

    def flushOutbuff(self, peer):  # for outputs
        try:
            msg = peer.outbuff.popleft()
            peer.socket.sendall(msg.encode())
            if msg != Peer.ACK_MESSAGE:
                peer.acks += 1
                self.log.debug(f'Expecting acknowledgement from "{peer.id}".')
        except:  # IndexError or OSError9
            pass

    def ack(self, peer):
        peer.outbuff.append(Peer.ACK_MESSAGE)
        self.log.debug(f'Acknowledgement sent to "{peer.id}".')

    def saveInbuff(self, peer):  # asserted read
        try:
            raw = peer.socket.recv(4096)  # asserted to end in special char
        except OSError as ex:
            self.log.error(f'Connection for {peer.id} is in an unrecoverable state: {ex}')
            self.closeSocket(peer)
            return

        if raw == b'':
            self.log.info(f'Socket closure requested by peer "{peer.id}".')
            self.closeSocket(peer)
            return

        for line in raw.split(Peer.ENDL_SYMBOL.encode()):
            self.log.debug(f'From {peer.id}: {line}')
            if peer.waitingAuth and line.startswith(Peer.HEAD_SYMBOL):  # asserted to be in anon list
                # auth message must be sent in a single tcp pakcet to avoid cutoffs
                peerId = line[1:].decode()
                self.log.info(f'Peer identified with name: "{peerId}"')
                peer.waitingAuth = False
                peer.id = peerId
                self.nameToFd.put(peerId, peer.socket.fileno())
                self.peers[peerId] = peer
                del self.anons[peer.socket.fileno()]
                self.ack(peer)
            elif line.startswith(Peer.ACK_SYMBOL):
                peer.acks -= 1
                self.log.debug(f'Acknowledgement received for "{peer.id}".')
            elif line == b'':
                pass
            else:
                try:
                    peer.inbuff.append(line.decode())
                    self.log.debug(f'Message appended to input buffer: {line.decode()}.')
                    self.ack(peer)
                except:
                    self.log.error(f'Inbound message dropped. Queue full. ({line.decode()})')
