import collections
import socket
import json


class Peer:
    GOOD = 444
    ANON = -2
    READY_TO_CONNECT = 0

    ACK_SYMBOL = b'\x06'
    HEAD_SYMBOL = '\x02'
    ENDL_SYMBOL = '\x1c'
    ACK_MESSAGE = ACK_SYMBOL.decode('ascii') + ENDL_SYMBOL # keep to minimum size of a single byte

    DEFAULT_EXT_ID = 'machine'
    DEFAULT_OUTPUT = json.loads('{}')

    def __init__(self, host, id, status, sckt, outbound=False):
        self.host = host  # tuple
        self.id = id  # string
        self.externalId = Peer.DEFAULT_EXT_ID
        self.status = status  # exclusive to outbound connections and anons
        self.outbuff = collections.deque([], 50)
        self.inbuff = collections.deque([], 50)
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
        self.outbuff.append(Peer.ACK_MESSAGE)

    def readline(self):
        instruction = Peer.DEFAULT_OUTPUT
        try:
            line = self.inbuff.popleft()
            instruction = json.loads(self.dangle + line)
        except IndexError:
            pass
        except ValueError:
            print(f'Invalid json: {line}')
            if self.dangle != '':
                self.dangle = ''
            else: # we trust the sendee to have sent a perfectly formatted mess
                self.dangle = line
        else:
            self.ack()
            self.dangle = ''
        return instruction

    def sendline(self, msg):
        try:
            self.outbuff.append(msg + Peer.ENDL_SYMBOL)
            print(f'Appended to outbuff: {msg}')
        except IndexError:
            pass

    def reset(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.status = Peer.READY_TO_CONNECT

    def addAuth(self):
        if self.outbound:
            self.outbuff.appendleft(f'{Peer.HEAD_SYMBOL}{self.externalId}{Peer.ENDL_SYMBOL}')

    def canConnect(self):
        if self.status == Peer.READY_TO_CONNECT or self.status == 119:
            return True
        else:
            return False

    def isFailed(self):
        if self.status != 115 and self.status != 106:
            return True
        else:
            return False
