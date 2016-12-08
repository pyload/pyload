# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
from os import remove
from os.path import dirname
from time import time
from shutil import move

import pycurl

from pyload.Api import Connection
from pyload.plugins.base import Abort
from pyload.network.cookiejar import CookieJar
from pyload.utils.fs import save_join, fs_encode

from ..download import Download
from .curlchunk import ChunkInfo, CurlChunk
from .curlrequest import ResponseException


# TODO: save content-disposition for resuming
class CurlDownload(Download):
    """ loads an url, http + ftp supported """

    # def __init__(self, url, filename, get={}, post={}, referer=None, cj=None, bucket=None,
    #              options={}, disposition=False):

    CONTEXT_CLASS = CookieJar

    def __init__(self, *args, **kwargs):
        Download.__init__(self, *args, **kwargs)

        self.path = None
        self.disposition = False

        self.chunks = []
        self.chunkSupport = None

        self.m = pycurl.CurlMulti()

        #needed for speed calculation
        self.lastArrived = []
        self.speeds = []
        self.lastSpeeds = [0, 0]

    @property
    def speed(self):
        last = [sum(x) for x in self.lastSpeeds if x]
        return old_div((sum(self.speeds) + sum(last)), (1 + len(last)))

    @property
    def arrived(self):
        return sum(c.arrived for c in self.chunks) if self.chunks else self._size

    @property
    def name(self):
        return self._name if self.disposition else None

    def _copyChunks(self):
        init = fs_encode(self.info.getChunkName(0)) #initial chunk name

        if self.info.getCount() > 1:
            fo = open(init, "rb+") #first chunkfile
            for i in range(1, self.info.getCount()):
                #input file
                fo.seek(
                    self.info.getChunkRange(i - 1)[1] + 1) #seek to beginning of chunk, to get rid of overlapping chunks
                fname = fs_encode("%s.chunk%d" % (self.path, i))
                fi = open(fname, "rb")
                buf = 32 * 1024
                while True: #copy in chunks, consumes less memory
                    data = fi.read(buf)
                    if not data:
                        break
                    fo.write(data)
                fi.close()
                if fo.tell() < self.info.getChunkRange(i)[1]:
                    fo.close()
                    remove(init)
                    self.info.remove() #there are probably invalid chunks
                    raise Exception("Downloaded content was smaller than expected. Try to reduce download connections.")
                remove(fname) #remove chunk
            fo.close()

        if self.name:
            self.path = save_join(dirname(self.path), self.name)

        move(init, fs_encode(self.path))
        self.info.remove() #remove info file

    def checkResume(self):
        try:
            self.info = ChunkInfo.load(self.path)
            self.info.resume = True #resume is only possible with valid info file
            self._size = self.info.size
            self.infoSaved = True
        except IOError:
            self.info = ChunkInfo(self.path)

    def download(self, uri, path, get={}, post={}, referer=True, disposition=False, chunks=1, resume=False, cookies=True):
        """ returns new filename or None """
        self.url = uri
        self.path = path
        self.disposition = disposition
        self.get = get
        self.post = post
        self.referer = referer
        self.cookies = cookies

        self.checkResume()
        chunks = max(1, chunks)
        resume = self.info.resume and resume

        try:
            self._download(chunks, resume)
        except pycurl.error as e:
            #code 33 - no resume
            code = e.args[0]
            if code == 33:
                # try again without resume
                self.log.debug("Errno 33 -> Restart without resume")

                #remove old handles
                for chunk in self.chunks:
                    self.closeChunk(chunk)

                return self._download(chunks, False)
            else:
                raise
        finally:
            self.close()

        return self.name

    def _download(self, chunks, resume):
        if not resume:
            self.info.clear()
            self.info.addChunk("%s.chunk0" % self.path, (0, 0)) #create an initial entry

        self.chunks = []

        init = CurlChunk(0, self, None, resume) #initial chunk that will load complete file (if needed)

        self.chunks.append(init)
        self.m.add_handle(init.getHandle())

        lastFinishCheck = 0
        lastTimeCheck = 0
        chunksDone = set()  # list of curl handles that are finished
        chunksCreated = False
        done = False
        if self.info.getCount() > 1: # This is a resume, if we were chunked originally assume still can
            self.chunkSupport = True

        while True:
            #need to create chunks
            if not chunksCreated and self.chunkSupport and self.size: #will be set later by first chunk

                self.flags ^= Connection.Resumable
                if not resume:
                    self.info.setSize(self.size)
                    self.info.createChunks(chunks)
                    self.info.save()

                chunks = self.info.getCount()

                init.setRange(self.info.getChunkRange(0))

                for i in range(1, chunks):
                    c = CurlChunk(i, self, self.info.getChunkRange(i), resume)

                    handle = c.getHandle()
                    if handle:
                        self.chunks.append(c)
                        self.m.add_handle(handle)
                    else:
                        #close immediately
                        self.log.debug("Invalid curl handle -> closed")
                        c.close()

                chunksCreated = True

            while True:
                ret, num_handles = self.m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            t = time()

            # reduce these calls
            # when num_q is 0, the loop is exited
            while lastFinishCheck + 0.5 < t:
                # list of failed curl handles
                failed = []
                ex = None # save only last exception, we can only raise one anyway

                num_q, ok_list, err_list = self.m.info_read()
                for c in ok_list:
                    chunk = self.findChunk(c)
                    try: # check if the header implies success, else add it to failed list
                        chunk.verifyHeader()
                    except ResponseException as e:
                        self.log.debug("Chunk %d failed: %s" % (chunk.id + 1, str(e)))
                        failed.append(chunk)
                        ex = e
                    else:
                        chunksDone.add(c)

                for c in err_list:
                    curl, errno, msg = c
                    chunk = self.findChunk(curl)
                    #test if chunk was finished
                    if errno != 23 or "0 !=" not in msg:
                        failed.append(chunk)
                        ex = pycurl.error(errno, msg)
                        self.log.debug("Chunk %d failed: %s" % (chunk.id + 1, str(ex)))
                        continue

                    try: # check if the header implies success, else add it to failed list
                        chunk.verifyHeader()
                    except ResponseException as e:
                        self.log.debug("Chunk %d failed: %s" % (chunk.id + 1, str(e)))
                        failed.append(chunk)
                        ex = e
                    else:
                        chunksDone.add(curl)
                if not num_q: # no more info to get

                    # check if init is not finished so we reset download connections
                    # note that other chunks are closed and everything downloaded with initial connection
                    if failed and init not in failed and init.c not in chunksDone:
                        self.log.error(_("Download chunks failed, fallback to single connection | %s" % (str(ex))))

                        #list of chunks to clean and remove
                        to_clean = [x for x in self.chunks if x is not init]
                        for chunk in to_clean:
                            self.closeChunk(chunk)
                            self.chunks.remove(chunk)
                            remove(fs_encode(self.info.getChunkName(chunk.id)))

                        #let first chunk load the rest and update the info file
                        init.resetRange()
                        self.info.clear()
                        self.info.addChunk("%s.chunk0" % self.path, (0, self.size))
                        self.info.save()
                    elif failed:
                        raise ex

                    lastFinishCheck = t

                    if len(chunksDone) >= len(self.chunks):
                        if len(chunksDone) > len(self.chunks):
                            self.log.warning("Finished download chunks size incorrect, please report bug.")
                        done = True  #all chunks loaded

                    break

            if done:
                break #all chunks loaded

            # calc speed once per second, averaging over 3 seconds
            if lastTimeCheck + 1 < t:
                diff = [c.arrived - (self.lastArrived[i] if len(self.lastArrived) > i else 0) for i, c in
                        enumerate(self.chunks)]

                self.lastSpeeds[1] = self.lastSpeeds[0]
                self.lastSpeeds[0] = self.speeds
                self.speeds = [old_div(float(a), (t - lastTimeCheck)) for a in diff]
                self.lastArrived = [c.arrived for c in self.chunks]
                lastTimeCheck = t

            if self.doAbort:
                raise Abort

            self.m.select(1)

        for chunk in self.chunks:
            chunk.flushFile() #make sure downloads are written to disk

        self._copyChunks()

    def findChunk(self, handle):
        """ linear search to find a chunk (should be ok since chunk size is usually low) """
        for chunk in self.chunks:
            if chunk.c == handle: return chunk

    def closeChunk(self, chunk):
        try:
            self.m.remove_handle(chunk.c)
        except pycurl.error as e:
            self.log.debug("Error removing chunk: %s" % str(e))
        finally:
            chunk.close()

    def close(self):
        """ cleanup """
        for chunk in self.chunks:
            self.closeChunk(chunk)
        else:
            #Workaround: pycurl segfaults when closing multi, that never had any curl handles
            if hasattr(self, "m"):
                c = pycurl.Curl()
                self.m.add_handle(c)
                self.m.remove_handle(c)
                c.close()

        self.chunks = []
        if hasattr(self, "m"):
            self.m.close()
            del self.m
        if hasattr(self, "info"):
            del self.info
