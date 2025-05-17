import bidict, logger, machine, peer_tcp, socket, select

socklog = logger.Logger('TCP-Sock', 'sockets.log')

# Socket declaration, it should be non-blocking
class Socker:
    def __init__(self, serverPort=None): # clientOpts is a tuple of (address[string], port[int])

        self.peers = { }
        self.nameToFd = bidict.BiMap()
        self.anons = { }
        
        self.server = None

        self.connector = select.poll()
        self.poller = select.poll()

        if serverPort:
            socklog.info('Initializing socket connector in server mode.')
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', serverPort))
            self.server.listen(1)
            self.server.setblocking(False)
            socklog.debug(f'Socket server bound to 0.0.0.0:{serverPort}')

            self.connector.register(self.server)
            
        socklog.info('Initializing socket connector in client mode.')
        
        # auto-updater 
        self.tim2 = machine.Timer(2)
        self.tim2.init(mode = machine.Timer.PERIODIC, freq = 5, callback = self._refresh) # better be 20hz


    def _refresh(self, t):
        if not self.poller.poll(1):
            if self.server: # can both act as server and client
                waiting = self.connector.poll(1)
                if waiting and waiting[0][1] & select.POLLIN:
                    client, address = waiting[0][0].accept()
                    client.setblocking(False)
                    socklog.info(f'Socket request accepted for {address}.')

                    self.anons[client.fileno()] = peer_tcp.Peer(None, "anon", -2, client)
                    self.poller.register(client) # authenticate anons first

            self.refreshPeerLinks()
        else:
            self.poll()
    
    def refreshPeerLinks(self):
        for k in self.peers:
            if not self.connect_ex(self.peers[k]):
                self.resetPeerLink(self.peers[k])
                # Unpolling/closing not necessary as it has been done by self.poll(), or never was polled/opened
        
    def resetPeerLink(self, peer):
        peer.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.socket.setblocking(False)
        peer.status = 0 # let connect_ex resart
        socklog.debug(f'Socket reset for peer "{peer.id}".')

    def connect_ex(self, peer): 
        if peer.status == 0 or peer.status == 119:
            socklog.debug(f'Connection attempt initiated to peer "{peer.id}".')
            try:
                peer.socket.connect(peer.host)
            except OSError as ex:
                peer.status = ex.errno
                socklog.debug(f'Connection attempt to peer "{peer.id}" status: {peer.status}.')
        elif not peer.status == 127:
            socklog.debug(f'Connection attempt failed to peer "{peer.id}": {peer.status}.')
            return False
        else:
            self.poller.register(peer.socket)
            self.peers[peer.id] = peer
            self.nameToFd.put(peer.id, peer.socket.fileno())
            socklog.info(f'Connected to peer "{peer.id}".')
        return True

    def closeSocket(self, peer):
        try:
            peer.socket.close()
        except:
            socklog.warn(f'An exception occurred while closing socket for peer {peer.id}.')
            pass
        self.poller.unregister(peer.socket)
        socklog.info(f'Connection closed for {s}.')

        if peer.status == -2: # Never authenticated
            del anon[peer.socket.fileno()]
            return
        elif peer.status == -1:
            del self.peers[peer.id] # Expecting peer-side reconnection to us (server)
        else:
            peer.status = 0 # Allow reconnection
        self.nameToFd.delByKey(peer.id) # Remove old fd reference

    def shutdown(self):
        self.tim2.deinit()
        socklog.info('Socket service shut down.')

    def poll(self):
        for s in self.poller.ipoll(1):
            peer = None
            if self.nameToFd.hasVal(s[0].fileno()):
                peer = self.peers[self.nameToFd.reverse[s[0].fileno()]]
            else:
                peer = self.anons[s[0].fileno()]
            
            if s[1] & select.POLLHUP or s[1] & select.POLLERR: # close socket and clear its references
                self.closeSocket(peer)
                socklog.error('Socket closed from errored state.')
            if s[1] & select.POLLIN:
                self.save_buffer(peer)
            if s[1] & select.POLLOUT:
                self.flush_buffer(peer)

    def flush_buffer(self, peer): # for outputs
        try:
            msg = peer.outbuff.popleft()
            peer.socket.sendall( msg.encode() )
            if msg != '\x06':
                self.acks += 1
                socklog.debug('Expecting message acknowledgement')
        except IndexError:
            pass

    def ack(self, peer):
        peer.outbuff.append('\x06')
        socklog.debug(f'Acknowledgement sent to {peer.id}.')

    def save_buffer(self, peer): # asserted read
        msg = bytearray() 

        try:
            raw = peer.socket.recv(1024) # asserted to end in special char
        except OSError as ex:
            socklog.error(f'Connection is in an unrecoverable state: {ex}')
            self.closeSocket(peer)
            return

        if raw == b'':
            socklog.info('Socket closure requested by peer.')
            self.closeSocket(peer)
            return

        for char in raw:
            if char == 10: # ascii LF 
                try:
                    peer.inbuff.append(msg.decode())
                    socklog.debug(f'Message appended to input buffer ({msg.decode()}.')
                    ack(peer)
                except:
                    socklog.error(f'Inbound message dropped. Queue full. ({msg.decode()})')
                msg = bytearray()
            elif char == 6: # ascii ACK 
                peer.acks -= 1
                socklog.debug(f'Acknowledgement received.')
            else:
                msg.extend(char.to_bytes(1))
        
    def readline(self, peer):
        line = ''
        try:
            line = peer.inbuff.popleft()
        except IndexError:
            pass
        return line

    def sendline(self, peer): 
        try:
            self.outbuff.append(msg + '\n')
        except IndexError:
            socklog.warn('Socket outbound message dropped. Queue full.')
