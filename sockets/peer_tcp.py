import collections, socket
class Peer:
    def __init__(self, host, id, status, sckt):
        self.host = host # tuple
        self.id = id # string
        self.status = status # int [0 for reconnecting on this side, -1 for not, -2 anon]
        self.outbuff = collections.deque([], 50, 1) 
        self.inbuff = collections.deque([], 50, 1)
        if sckt == None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setblocking(False)
        else:
            self.socket = sckt
            self.socket.setblocking(False)
        self.waitingAuth = False
