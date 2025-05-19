from ubinascii import a2b_base64
import _thread
import machine


class Commander:
    CHUNK_SIZE = 384  # 384 bytes from 512 bytes of base64 encoded data
    def __init__(self, socker):
        #
        self.socker = socker
        self.masters = [] # to read from
        self.slaves = [] # to input to
        self.files = {}

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

    def acceptFile(self, obj, caller):
        seq = obj['seq']
        fid = obj['fid']
        lng = obj['len']
        fin = obj['fin']
        if seq == 1:
            self.files[fid] = bytearray(lng)
        self.files[fid][(seq - 1) * Commander.CHUNK_SIZE:seq*Commander.CHUNK_SIZE - 1] = a2b_base64(obj['dat'])
        if fin == 1:
            # wrap up and save to disk
            _thread.start_new_thread(self._saveToDisk, (fid,))
            #self._saveToDisk(fid)
            
    def _saveToDisk(self, fid):
        with open(fid, 'w') as f:
            f.write(self.files[fid])
        del self.files[fid]
