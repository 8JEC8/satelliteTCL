import collections, logger, machine, socket, select

socklog = logger.Logger('TCP-Sock', 'sockets.log')

# Socket declaration, it should be non-blocking
class Socker:
    def __init__(self, port=None, clientOpts=None): # clientOpts is a tuple of (address[string], port[int])
        self.active = False

        self.buffer = collections.deque([], 50, 1)
        self.outbuff = collections.deque([], 50, 1)

        # Maybe do a security buffer queue? And pop as we receive acks

        self.code = 0
       
        self.server = None
        self.peersocket = None 
        self.clientOpts = clientOpts

        self.connector = select.poll()
        self.peer = select.poll()

        if clientOpts:
            socklog.info('Initializing socket connector in client mode.')
            self.resetPeerLink()
        else:
            socklog.info('Initializing socket connector in server mode.')
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(('', port))
            self.server.listen(1)
            self.server.setblocking(False)
            socklog.debug(f'Socket server bound to 0.0.0.0:{port}')

            self.connector.register(self.server)

        # auto-updater 
        self.tim2 = machine.Timer(2)
        self.tim2.init(mode = machine.Timer.PERIODIC, freq = 5, callback = self._refresh) # better be 20hz


    def _refresh(self, t):
        if not self.peer.poll(1): # nothing writable, nothing errored
            if self.server:
                waiting = self.connector.poll(1)
                if waiting and waiting[0][1] & select.POLLIN:
                    client, address = waiting[0][0].accept()
                    client.setblocking(False)
                    socklog.info(f'Socket request accepted for {address}.')

                    self.peer.register(client)
            else:
                self.refreshPeerLink()
        else:
            self.poll()
    
    def refreshPeerLink(self):
        if not self.connect_ex(self.peersocket, self.clientOpts):
            self.resetPeerLink()
            # Unpolling/closing not necessary as it has been done by self.poll(), or never was polled/opened
        
    def resetPeerLink(self):
        self.peersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peersocket.setblocking(False)
        self.code = 0 # let connect_ex resart
        socklog.info('Peer link reset. (Client mode)')

    def connect_ex(self, s, address): 
        if self.code == 0 or self.code == 119:
            socklog.info('Connection attempt launched')
            try:
                s.connect(address)
            except OSError as ex:
                self.code = ex.errno
                socklog.info(f'Status code: {self.code}')
        elif not self.code == 127:
            socklog.warn(f'Connection failed with code {self.code}')
            return False
        else:
            self.peer.register(s)
            self.acive(True)
            socklog.warn(f'Connection accepted. Socket registered')
        return True

    def closeSocket(self, s):
        try:
            #s.shutdown()
            s.close()
        except:
            socklog.warn('An exception occurred while closing socket.')
            pass
        self.peer.unregister(s)
        self.code = 0 # Allow reconnection
        socklog.info('Socket closed. Peer disconnection.')
        self.active = False

    def shutdown(self):
        self.tim2.deinit()
        socklog.info('Socket service shut down.')

    acks = 0 # Should ideally be zero

    def poll(self):
        for s in self.peer.ipoll(1):
            if s[1] & select.POLLHUP or s[1] & select.POLLERR: # close socket and clear its references
                self.closeSocket(s[0])
            if s[1] & select.POLLIN:
                self.save_buffer(s[0])
            if s[1] & select.POLLOUT:
                self.flush_buffer(s[0])
                self.active = True

    def flush_buffer(self, s): # for outputs
        try:
            msg = self.outbuff.popleft()
            s.sendall( msg.encode() )
            if msg != '\x06':
                self.acks += 1
                socklog.debug('Expecting message acknowledgement')
        except IndexError:
            pass

    def ack(self):
        self.outbuff.append('\x06')
        socklog.debug('Acknowledgement sent.')

    def save_buffer(self, s): # asserted read
        msg = bytearray() 
        raw = s.recv(1024) # asserted to end in special char

        if raw == b'':
            socklog.info('Socket closure requested by peer.')
            self.closeSocket(s)
            return

        for char in raw:
            if char == 10: # ascii LF 
                try:
                    self.buffer.append(msg.decode())
                    socklog.debug(f'Message appended to input buffer ({msg.decode()}.')
                    self.ack()
                except:
                    socklog.error(f'Inbound message dropped. Queue full. ({msg.decode()})')
                msg = bytearray()
            elif char == 6: # ascii ACK 
                self.acks -= 1
                socklog.debug(f'Acknowledgement received.')
            else:
                msg.extend(char.to_bytes(1))
        
    def readline(self):
        line = ''
        try:
            line = self.buffer.popleft()
        except IndexError:
            pass
        return line

    def sendline(self, msg): 
        if self.active:
            try:
                self.outbuff.append(msg + '\n')
            except IndexError:
                socklog.warn('Socket outbound message dropped. Queue full.')
        else:
            socklog.warn('Socket outbound message ignored. No peers online.')
            pass
