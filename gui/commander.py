#
#   UNIX VERSION
#
from base64 import b64encode, b64decode
from logger import Logger
import json
import math
import os
import time, threading


class Command:
    def __init__(self):
        # nothing
        self.opts = {}

    def ofKindAcceptFile(self, filename, binarysize):
        self.opts['seq'] = 1
        self.opts['cmd'] = 'acceptFile'
        self.opts['fid'] = filename 
        self.opts['len'] = binarysize
        self.opts['fin'] = 0
        self.opts['dat'] = bytearray(Commander.CHUNK_SIZE_B64)

    def ofKindSyncTime(self, time):
        self.opts['cmd'] = 'time'
        self.opts['tim'] = time  # from Y2K epoch

    def ofKindGiveFile(self, filename):
        self.opts['cmd'] = 'reqFile'
        self.opts['fid'] = filename
    
    def ofKindToggleLed(self):
        self.opts['cmd'] = 'led'

    def ofKindReqFiles(self):
        self.opts['cmd'] = 'ls'


class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    CHUNK_SIZE_B64 = 512
    def __init__(self, socker):
        self.log = Logger('Commands', 'cmdloop.log')
        self.phyStatus = [(0,0), (0,0), (0,0,0), (0,), (0,)]
        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}
        self.filesOutMeta = {}

    def _refresh(self):
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
        threading.Timer(.001, self._refresh).start()

    def handleRequestLed(self, ledOwner):
        instrucObj = Command()
        instrucObj.ofKindToggleLed()
        self.socker.peers[ledOwner].sendline(json.dumps(instrucObj.opts))

    def handleRequestFile(self, provider, fid):
        instrucObj = Command()
        instrucObj.ofKindGiveFile(fid)
        self.socker.peers[provider].sendline(json.dumps(instrucObj.opts))

    def handleCommand(self, obj, caller):  # skipping file size check
        if obj['cmd'] == 'acceptFile':
            self.acceptFile(obj, caller)
        elif obj['cmd'] == 'reqFile':
            _thread.start_new_thread(self._readFromDisk, (fid, caller))
            self.sendFile(obj, caller)
        elif obj['cmd'] == 'acceptStatus':
            self.commandReadStats(obj)
        elif obj['cmd'] == 'lsRes':
            self.handleLsRes(obj)

    def syncTime(self, peer):
        print(f'Sending {peer.id} the current time...')
        instrucObj = Command()
        instrucObj.ofKindSyncTime(int(time.time()) - 946684800)
        peer.handShaken = True
        peer.sendline(json.dumps(instrucObj.opts))

    def acceptFile(self, obj, caller):
        print(f"Accepted file chunk: {obj['seq']}/{obj['fid']}")
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 0:
            self.files[fid] = open(fid, 'wb')
        self.files[fid].write(b64decode(obj['dat']))
        if fin == 1:
            self.files[fid].close()
            del self.files[fid]
            self.log.info(f'Finished downloading {obj["fid"]} ({obj["len"]})B')

    def sendFile(self, destination, fid): # assuming peer exists. can be used for first invocation as well as recurring refreshes
        #print('Started file transmission')
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
                instrucObj.opts['dat'] = b64encode(self.files[fid].read(Commander.CHUNK_SIZE)).decode('ascii')

                if seq >= lastSeq:
                    instrucObj.opts['fin'] = 1
                    self.files[fid].close()
                    del self.files[fid]
                    del self.filesOutMeta[fid]
                else:
                    self.filesOutMeta[fid][3] += 1

                receiver.sendline(json.dumps(instrucObj.opts))
                print(f'Dispatched seq {seq} @ commander.py')


    def _readFromDisk(self, fid):
            # assuming we do have the file (skipping request denial for now)
            try:
                filesize = os.stat(fid)[6]
            except OSError:
                del self.filesOutMeta[fid]
                return

            self.files[fid] = open(fid, 'rb')

            last_sequence = math.ceil(filesize / Commander.CHUNK_SIZE)

            self.filesOutMeta[fid][0] = filesize
            self.filesOutMeta[fid][1] = last_sequence - 1
            self.filesOutMeta[fid][3] = 0

    def readStatus(self):
        return self.phyStatus

    def commandReadStats(self, obj):
        self.phyStatus[0] = (obj['tmp'][0], obj['tmp'][1])
        self.phyStatus[1] = (obj['pwr'][0], obj['pwr'][1])
        self.phyStatus[2] = (obj['gyr'][0], obj['gyr'][1], obj['gyr'][2])
        self.phyStatus[3] = (obj['ssi'],)
        self.phyStatus[4] = (obj['led'],)

    def handleLsRes(self, obj):
        self.log.info(f'Files in root: {obj['root']}')
        self.log.info(f'Files in SD card: {obj['sd']}')

    def commandReqFiles(self, filee):
        instrucObj = Command()
        instrucObj.ofKindReqFiles()
        peer = self.socker.peers[filee]
        peer.sendline(json.dumps(instrucObj.opts))
        
