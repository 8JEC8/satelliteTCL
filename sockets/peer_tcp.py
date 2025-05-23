import collections
import socket
import json


class Peer:
    GOOD = 444
    ANON = -2
    READY_TO_CONNECT = 0

    ACK_SYMBOL = b'\x06'
    HEAD_SYMBOL = b'\x02'
    ENDL_SYMBOL = b'\x1c'
    ACK_MESSAGE = ACK_SYMBOL.decode('ascii')

    DEFAULT_EXT_ID = 'machine'
    DEFAULT_OUTPUT = json.loads('{}')

    def __init__(self, host, id, status, sckt, outbound=False):
        self.host = host  # tuple
        self.id = id  # string
        self.externalId = Peer.DEFAULT_EXT_ID
        self.status = status  # exclusive to outbound connections and anons
        self.outbuff = bytearray()
        self.inbuff = collections.deque([], 50, 1)
        self.outbound = outbound
        self.waitingAuth = False
        self.dangle = ''
        self.acks = 0

        if sckt is None:
            self.reset()
        else:
            self.socket = sckt
            self.socket.setblocking(False)

        if status == Peer.ANON:
            self.waitingAuth = True

    def setExternalId(self, externalId):
        self.externalId = externalId

    def ack(self):
        self.outbuff.extend(Peer.ACK_SYMBOL + Peer.ENDL_SYMBOL)

    def readline(self):
        instruction = Peer.DEFAULT_OUTPUT
        try:
            line = self.inbuff.popleft()
            instruction = json.loads(self.dangle + line)
        except IndexError:
            pass
        except ValueError:
            if self.dangle != '':
                print(f'Malformed json. Dropping string: {self.dangle + line}')
                self.dangle = ''
            else: # we trust the sendee to have sent a perfectly formatted mess
                self.dangle = line
        else:
            self.ack()        # message processed
            self.dangle = ''  # successful recovery
        return instruction

    def sendline(self, msg):
        try:
            self.outbuff.extend(msg.encode() + Peer.ENDL_SYMBOL)
            self.acks += 1
        except IndexError:
            pass

    def reset(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.status = Peer.READY_TO_CONNECT

    def addAuth(self):
        if self.outbound:
            authMsg = Peer.HEAD_SYMBOL + self.externalId.encode() + Peer.ENDL_SYMBOL
            if not self.outbuff.startswith(authMsg):
                self.outbuff = bytearray(authMsg) + self.outbuff
                self.acks += 1

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
