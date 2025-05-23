from ubinascii import a2b_base64, b2a_base64
import json
import math
import os


class Command:  # TODO: Style and readabilty
    def __init__(self):
        self.opts = {}

    def ofKindStatsReply(self):
        self.opts['cmd'] = 'acceptStatus'
        self.opts['ssi'] = 0  # db
        self.opts['tmp'] = (32, 69)  # celsius, humidity
        self.opts['gyr'] = (44, 90, 101)  # x, y, z
        self.opts['pwr'] = (5, 0.5)  # volt, amp

    def ofKindAcceptFile(self, filename, binarysize):
        self.opts['seq'] = 1
        self.opts['cmd'] = 'acceptFile'
        self.opts['fid'] = filename 
        self.opts['len'] = binarysize
        self.opts['fin'] = 0
        self.opts['dat'] = bytearray(Commander.CHUNK_SIZE_B64)
        

class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    CHUNK_SIZE_B64 = 512
    def __init__(self, socker):
        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}
        self.filesOutMeta = {}

    def _refresh(self, t):
        pendingFiles = self.filesOutMeta.copy().keys()
        for f in pendingFiles:  # some entires might disappear after being processed
            self.sendFile(self.filesOutMeta[f][2], f)

        for s in self.slaves:
            try:
                peer = self.socker.peers[s]
            except KeyError:
                continue

        for m in self.masters:
            try:
                peer = self.socker.peers[m]
            except KeyError:
                continue

            a =  peer.readline()
            if len(a) == 0:
                continue

            self.handleCommand(a, m)

    def handleCommand(self, obj, caller):  # skipping file size check
        if obj['cmd'] == 'acceptFile':
            self.acceptFile(obj, caller)
        elif obj['cmd'] == 'reqFile':
            self._readFromDisk(fid, caller)
            self.sendFile(obj, caller)
        elif obj['cmd'] == 'reqStatus':
            self.commandStats(self, caller)
        elif obj['cmd'] == 'acceptStatus':
            self.commandReadStats(obj)

    def acceptFile(self, obj, caller):
        print(f"Accepted file chunk: {obj['seq']}/{obj['fid']}")
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 0:
            self.files[fid] = bytearray(lng)
        self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq * Commander.CHUNK_SIZE] = a2b_base64(obj['dat'])
        if fin == 1:
            #_thread.start_new_thread(self._saveToDisk, (fid,))
            self._saveToDisk(fid)

    def sendFile(self, destination, fid):
        #_thread.start_new_thread(self._readFromDisk, (fid, destination))

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
                instrucObj.opts['dat'] = b2a_base64(self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq * Commander.CHUNK_SIZE]).decode('ascii')

                if seq >= lastSeq:
                    instrucObj.opts['fin'] = 1
                    del self.files[fid]
                    del self.filesOutMeta[fid]
                else:
                    self.filesOutMeta[fid][3] += 1

                receiver.sendline(json.dumps(instrucObj.opts))
                print(f'Dispatched seq {seq} @ commander.py')
            
    def _saveToDisk(self, fid):
        with open(fid, 'wb') as f:
            f.write(self.files[fid])
        del self.files[fid]

    def _readFromDisk(self, fid):  # TODO: File request rejection
            try:
                filesize = os.stat(fid)[6]
            except OSError:
                return
            with open(fid, 'rb') as f:
                self.files[fid] = f.read()

            last_sequence = math.ceil(filesize / Commander.CHUNK_SIZE)

            self.filesOutMeta[fid][0] = filesize
            self.filesOutMeta[fid][1] = last_sequence
            self.filesOutMeta[fid][3] = 0

    def commandStats(self, caller):
        peer = self.socker.peers[caller]
        obj = Command()
        obj.ofKindStatsReply()
        peer.sendline(json.dumps(obj.opts))

    def commandReadStats(self, obj):
        print(f'RSSI.. {obj['ssi']}dB')
        print(f'Temp./Humid.. {obj['tmp'][0]}deg / {obj['tmp'][1]}%')
        print(f'Gyro.. x:{obj['gyr'][0]} y:{obj['gyr'][1]} z:{obj['gyr'][2]}')
        print(f'Pow.. {obj['pwr'][0]}V {obj['pwr'][1]}A')
