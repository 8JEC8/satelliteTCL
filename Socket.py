import socket

class ClientSock:
    def __init__(self):
        #
    def connect():
        #
    def send():
        #
    def receive():
        #

class ServerSock:
    def __init__(self):
        #
    def accept():


# run this loop every 100 ms to check for new data
for i in poll.ipoll(1): # 1ms, and i am being generous
    sock = socket.fromfd(i[0], socket.AF_INET, socket.SOCK_STREAM)
