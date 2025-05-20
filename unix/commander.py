import base64
import json
import math
import os


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
        #
        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}
        self.fileStats = {}  # save current status of outbound files

    def _refresh(self):
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

    def acceptFile(self, obj, caller):
        print(f"Accepted file chunk: {obj['seq']}/{obj['fid']}")
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 1:
            self.files[fid] = bytearray(lng)
        self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq * Commander.CHUNK_SIZE] = base64.b64decode(obj['dat'])
        if fin == 1:
            # wrap up and save to disk
            self._saveToDisk(fid)
            #self._saveToDisk(fid)

    def sendFile(self, destination, fid): # assuming peer exists
        print('Started file transmission')
        self._readFromDisk(fid, destination)
            
    def _saveToDisk(self, fid):
        with open(fid, 'wb') as f:
            f.write(self.files[fid])
        del self.files[fid]

    def _readFromDisk(self, fid, caller):
            # assuming we do have the file (skipping request denial for now)
            try:
                filesize = os.stat(fid)[6]
            except OSError:
                return
            with open(fid, 'rb') as f:
                self.files[fid] = f.read()

            instrucObj = Command()
            instrucObj.ofKindAcceptFile(fid, filesize)

            upperbound = math.ceil(filesize / Commander.CHUNK_SIZE)

            for i in range(1, upperbound + 1):
                instrucObj.opts['seq'] = i
                instrucObj.opts['dat'] = base64.b64encode(self.files[fid][(i - 1) * Commander.CHUNK_SIZE:i * Commander.CHUNK_SIZE])
                if i == upperbound:
                    instrucObj.opts['fin'] = 1
                self.socker.peers[caller].sendline(json.dumps(instrucObj.opts))

            del self.files[fid]
