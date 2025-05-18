import collections
import socket
class Peer:
    def __init__(self, host, id, status, sckt, outbound=False):
        self.host = host # tuple
        self.id = id # string
        self.status = status # exclusive to outbound connections and anons
        self.outbuff = collections.deque([], 50, 1) 
        self.inbuff = collections.deque([], 50, 1)
        self.outbound = outbound
        self.waitingAuth = False
        self.acks = 0

        if sckt == None:
            self.reset(0)
        else:
            self.socket = sckt
            self.socket.setblocking(False)

        if status == -2:
            self.waitingAuth = True

    def readline(self):
        line = ''
        try:
            line = self.inbuff.popleft()
        except IndexError:
            pass
        return line

    def sendline(self, msg): 
        try:
            self.outbuff.append(msg + '\n')
        except IndexError:
            pass

    def reset(self, status):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.status = status

    def addAuth(self):
        if self.outbound:
            #reset acks?
            self.outbuff.appendleft(f'\x02{self.id}\n')

