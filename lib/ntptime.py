#
#   Retrieved from github.com/micropython/micropython-lib
#   'NTP client' module
#   '0.1.1' version
#
from time import gmtime
import socket
import struct

host = "pool.ntp.org"
timeout = 1

def time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]

    # 2024-01-01 00:00:00 converted to an NTP timestamp
    MIN_NTP_TIMESTAMP = 3913056000

    if val < MIN_NTP_TIMESTAMP:
        val += 0x100000000

    EPOCH_YEAR = gmtime(0)[0]
    if EPOCH_YEAR == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 2208988800
    else:
        raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

    return val - NTP_DELTA

# There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
def settime():
    t = time()
    import machine

    tm = gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
