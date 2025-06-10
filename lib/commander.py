from network_interface import Nif
try:
    from ina219 import INA219
    from mpu6050 import MPU6050
    from sth31 import read_sth31
except ImportError:
    pass
from ubinascii import a2b_base64, b2a_base64
from logger import Logger
import gc
import json
import machine
import math
import os

'''
Commands created using this class are not initiators,
but represent the structure used for data transfer.
'''
class Command:  # TODO: Style and readabilty
    def __init__(self):
        self.opts = {}

    def ofKindStatsReply(self):
        try:
            self.opts['cmd'] = 'acceptStatus'
            self.opts['ssi'] = Nif.sta.status('rssi')  # db
            self.opts['tmp'] = read_sth31(Commander.i2c)
            self.opts['gyr'] = Commander.mpu.get_raw_gyro()
            self.opts['pwr'] = (Commander.ina.bus_voltage, Commander.ina.current)
            self.opts['led'] = Commander.led.value()
        except NameError:
            pass

    def ofKindReqStats(self):
        self.opts['cmd'] = 'reqStatus'

    def ofKindAcceptFile(self, filename, binarysize):
        self.opts['seq'] = 1
        self.opts['cmd'] = 'acceptFile'
        self.opts['fid'] = filename 
        self.opts['len'] = binarysize
        self.opts['fin'] = 0
        self.opts['dat'] = bytearray(Commander.CHUNK_SIZE_B64)

    def ofKindGenericErorr(self, errorMsg):
        self.opts['cmd'] = 'error'
        self.opts['msg'] = errorMsg

    def ofKindGiveFile(self, filename):
        self.opts['cmd'] = 'reqFile'
        self.opts['fid'] = filename

    def ofKindSyncTime(self, time):
        self.opts['cmd'] = 'time'
        self.opts['tim'] = time  # from Y2K epoch

    def ofKindToggleLed(self):
        self.opts['cmd'] = 'led'

    def ofKindListDir(self):
        self.opts['cmd'] = 'lsRes'
        self.opts['root'] = None
        self.opts['sd'] = None


class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    CHUNK_SIZE_B64 = 512
    fullmode = False
    spi = None
    i2c = None
    ina = None
    mpu = None
    led = machine.Pin(33, machine.Pin.OUT) #LED, Pin D33
    def __init__(self, socker):
        self.log = Logger('Commands')

        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}
        self.filesOutMeta = {}
        self.counterFiveHundred = 0 

        # stats command initialization
        try:
            Commander.spi = machine.SPI(1,
                                   baudrate=5000000,
                                   polarity=0,
                                   phase=0,
                                   sck=machine.Pin(18),
                                   mosi=machine.Pin(23),
                                   miso=machine.Pin(19))
            Commander.i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000, timeout=1000)
            Commander.ina = INA219(Commander.i2c)
            Commander.mpu = MPU6050(Commander.i2c)
            Commander.fullmode = True
        except NameError:
            pass

    def _refresh(self, t):
        if Commander.fullmode:
            self.counterFiveHundred += 1
        if self.counterFiveHundred < 100:  # pause file sending if status is due
            pendingFiles = self.filesOutMeta.copy().keys()
            for f in pendingFiles:  # some entires might disappear after being processed
                self.handleSendFile(self.filesOutMeta[f][2], f)

        for m in self.masters:
            try:
                peer = self.socker.peers[m]
            except KeyError:
                continue

            if self.counterFiveHundred >= 100:
                self.handleReqStats(peer)

            a =  peer.readline()
            if len(a) == 0:
                continue

            self.handleCommand(a, m)

        gc.collect()

    def handleCommand(self, obj, caller):  # skipping file size check
        try:
            if obj['cmd'] == 'acceptFile':
                self.handleAcceptFile(obj, caller)
            elif obj['cmd'] == 'reqFile':
                self.handleSendFile(caller, obj['fid'])
            elif obj['cmd'] == 'acceptStatus':
                self.commandReadStats(obj)
            elif obj['cmd'] == 'time':
                self.handleSynctime(obj)
            elif obj['cmd'] == 'led':
                self.handleToggleLed()
            elif obj['cmd'] == 'ls':
                self.handleReqFiles(caller)
        except Exception as e:
            self.log.error(f'{e}')

    def handleSyncTime(self, obj):
        import machine
        import time
        tm = time.gmtime(obj[tim])
        print('Syncing time...')
        machine.RTC().datetime((tm[0], tm[1], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        print('Time synced')

    def handleSendSyncTime(self, peer):
        import time
        instrucObj = Command()
        instrucObj.ofKindSyncTime(time.time())
        peer.sendline(json.dumps(instrucObj.opts))
        print(f'Sent time sync request to {peer.id}')

    def handleAcceptFile(self, obj, caller):  # TODO: IMPLEMENTATION INCOMPLETE-----------------------------
        print(f"Accepted file chunk: {obj['seq']}/{obj['fid']}")
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 0:
            self.files[fid] = open(fid, 'wb')
        self.files[fid].write(a2b_base64(obj['dat']))
        if fin == 1:
            self.files[fid].close()
            del self.files[fid]
            self.log.info(f'Finished downloading {fid}')

    def handleSendFile(self, destination, fid):
        if self.filesOutMeta.get(fid) is None:
            self.filesOutMeta[fid] = [None, None, destination, None] #filesize,  lastSeq, caller, currentSeq
            self._readFromDisk(fid)
            return
        
        if self.filesOutMeta[fid][0] is not None:
            fileSize, lastSeq, caller, seq = self.filesOutMeta[fid]
            instrucObj = Command()
            instrucObj.ofKindAcceptFile(fid, fileSize)

            receiver = self.socker.peers[caller]

            if receiver.acks < 4:
                instrucObj.opts['seq'] = seq
                instrucObj.opts['dat'] = b2a_base64(self.files[fid].read(Commander.CHUNK_SIZE)).decode('ascii')

                if seq >= lastSeq:
                    instrucObj.opts['fin'] = 1
                    self.files[fid].close()  # remove our lock, if that's even a thing here
                    del self.files[fid]
                    del self.filesOutMeta[fid]
                else:
                    self.filesOutMeta[fid][3] += 1

                receiver.sendline(json.dumps(instrucObj.opts))
                print(f'Dispatched seq {seq} @ commander.py')
            
    def _readFromDisk(self, fid):  # TODO: File request rejection
            try:
                filesize = os.stat(fid)[6]
            except OSError:
                del self.filesOutMeta[fid]
                return

            self.files[fid] = open(fid, 'rb')  # assigned pointer to file start 

            last_sequence = math.ceil(filesize / Commander.CHUNK_SIZE)

            self.filesOutMeta[fid][0] = filesize
            self.filesOutMeta[fid][1] = last_sequence - 1
            self.filesOutMeta[fid][3] = 0

    def handleReqStats(self, peer):
        if peer.acks < 4:
            obj = Command()
            obj.ofKindStatsReply()
            peer.sendline(json.dumps(obj.opts))
            self.counterFiveHundred = 0

    def handleToggleLed(self):
        bn = [1, 0]
        Commander.led.value(bn[Commander.led.value()])

    def handleReqFiles(self, callerName):
        caller = self.socker.peers[callerName]
        instrucObj = Command()
        instrucObj.ofKindListDir()
        instrucObj.opts['root'] = os.listdir()
        instrucObj.opts['sd'] = []
        try:
            instrucObj.opts['sd'] = os.listdir('sd')
        except OSError:
            pass
        caller.sendline(json.dumps(instrucObj.opts))


