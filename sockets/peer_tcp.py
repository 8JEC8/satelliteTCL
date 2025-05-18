import collections
import socket
class Peer:
    GOOD = 444
    ANON = -2
    READY_TO_CONNECT = 0
    
    ACK_SYMBOL = '\x06'
    HEAD_SYMBOL = '\x02'
    ENDL_SYMBOL = '\n'
    ACK_MESSAGE = ACK_SYMBOL + ENDL_SYMBOL

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
            self.reset()
        else:
            self.socket = sckt
            self.socket.setblocking(False)

        if status == Peer.ANON:
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

    def reset(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.status = Peer.READY_TO_CONNECT

    def addAuth(self):
        if self.outbound:
            #reset acks?
            self.outbuff.appendleft(f'\x02{self.id}\n')

    def canConnect(self):
        if self.status == Peer.READY_TO_CONNECT or self.status == 119:
            return True
        else:
            return False

    def isFailed(self):
        if self.status != 127 and self.status != 120:
            return True 
        else:
            return False 

