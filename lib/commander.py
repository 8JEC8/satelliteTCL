from network_interface import Nif
from ubinascii import a2b_base64, b2a_base64
import gc
import json
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
        self.opts['cmd'] = 'acceptStatus'
        self.opts['ssi'] = Nif.sta.status('rssi')  # db
        self.opts['tmp'] = (32, 69)  # celsius, humidity
        self.opts['gyr'] = (44, 90, 101)  # x, y, z
        self.opts['pwr'] = (5, 0.5)  # volt, amp

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


class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    CHUNK_SIZE_B64 = 512
    def __init__(self, socker):
        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}
        self.filesOutMeta = {}
        self.counterFiveHundred = 0 

    def _refresh(self, t):
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

    def handleCommand(self, obj, caller):  # skipping file size check
        if obj['cmd'] == 'acceptFile':
            self.handleAcceptFile(obj, caller)
        elif obj['cmd'] == 'reqFile':
            self.handleSendFile(caller, obj['fid'])
        elif obj['cmd'] == 'acceptStatus':
            self.commandReadStats(obj)
        elif obj['cmd'] == 'time':
            self.handleSynctime(obj)

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

    def handleAcceptFile(self, obj, caller):
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

    def handleSendFile(self, destination, fid):
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
                    gc.collect()
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

    def handleReqStats(self, peer):
        if peer.acks < 4:
            obj = Command()
            obj.ofKindStatsReply()
            peer.sendline(json.dumps(obj.opts))
            self.counterFiveHundred = 0
