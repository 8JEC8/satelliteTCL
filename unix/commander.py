#
#   UNIX VERSION
#
from base64 import b64encode, b64decode
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
        

class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    CHUNK_SIZE_B64 = 512
    def __init__(self, socker):
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

    def handleCommand(self, obj, caller):  # skipping file size check
        if obj['cmd'] == 'acceptFile':
            self.acceptFile(obj, caller)
        elif obj['cmd'] == 'reqFile':
            _thread.start_new_thread(self._readFromDisk, (fid, caller))
            self.sendFile(obj, caller)

    def acceptFile(self, obj, caller):
        print(f"Accepted file chunk: {obj['seq']}/{obj['fid']}")
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 0:
            self.files[fid] = bytearray(lng)
        self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq * Commander.CHUNK_SIZE] = b64decode(obj['dat'])
        if fin == 1:
            # wrap up and save to disk
            #_thread.start_new_thread(self._saveToDisk, (fid,))
            self._saveToDisk(fid)

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
                instrucObj.opts['dat'] = b64encode(self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq * Commander.CHUNK_SIZE]).decode('ascii')

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

    def _readFromDisk(self, fid):
            # assuming we do have the file (skipping request denial for now)
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
