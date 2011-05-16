#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
"""

from os import remove, fsync
from os.path import dirname
from time import sleep, time
from shutil import move

import pycurl

from HTTPChunk import ChunkInfo, HTTPChunk
from HTTPRequest import BadHeader

from module.plugins.Plugin import Abort
from module.utils import save_join

class HTTPDownload():
    """ loads a url http + ftp """
    def __init__(self, url, filename, get={}, post={}, referer=None, cj=None, bucket=None,
                 options={}, progressNotify=None, disposition=False):
        self.url = url
        self.filename = filename  #complete file destination, not only name
        self.get = get
        self.post = post
        self.referer = referer
        self.cj = cj  #cookiejar if cookies are needed
        self.bucket = bucket
        self.options = options
        self.disposition = disposition
        # all arguments

        self.abort = False
        self.size = 0
        self.nameDisposition = None #will be parsed from content disposition

        self.chunks = []

        try:
            self.info = ChunkInfo.load(filename)
            self.info.resume = True #resume is only possible with valid info file
            self.size = self.info.size
            self.infoSaved = True
        except IOError:
            self.info = ChunkInfo(filename)

        self.chunkSupport = None
        self.m = pycurl.CurlMulti()

        #needed for speed calculation
        self.lastChecked = 0
        self.lastArrived = []
        self.speeds = []
        self.lastSpeeds = [0, 0]
        
        self.progressNotify = progressNotify

    @property
    def speed(self):
        last = [sum(x) for x in self.lastSpeeds if x]
        return (sum(self.speeds) + sum(last)) / (1 + len(last))

    @property
    def arrived(self):
        return sum([c.arrived for c in self.chunks])

    @property
    def percent(self):
        if not self.size: return 0
        return (self.arrived * 100) / self.size

    def _copyChunks(self):
        init = self.info.getChunkName(0) #initial chunk name

        if self.info.getCount() > 1:
            fo = open(init, "rb+") #first chunkfile
            for i in range(1, self.info.getCount()):
                #input file
                fo.seek(self.info.getChunkRange(i - 1)[1] + 1) #seek to beginning of chunk, to get rid of overlapping chunks
                fname = "%s.chunk%d" % (self.filename, i)
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

        if self.nameDisposition and self.disposition:
            self.filename = save_join(dirname(self.filename), self.nameDisposition)
            
        move(init, self.filename)
        self.info.remove() #remove info file

    def download(self, chunks=1, resume=False):
        """ returns new filename or None """

        chunks = max(1, chunks)
        resume = self.info.resume and resume
        self.chunks = []

        try:
            self._download(chunks, resume)
        finally:
            self.close()

        if self.nameDisposition and self.disposition: return self.nameDisposition
        return None

    def _download(self, chunks, resume):
        if not resume:
            self.info.clear()
            self.info.addChunk("%s.chunk0" % self.filename, (0, 0)) #create an initial entry

        init = HTTPChunk(0, self, None, resume) #initial chunk that will load complete file (if needed)

        self.chunks.append(init)
        self.m.add_handle(init.getHandle())

        chunksDone = 0
        chunksCreated = False
        if self.info.getCount() > 1: # This is a resume, if we were chunked originally assume still can
            self.chunkSupport=True

        while 1:
            #need to create chunks
            if not chunksCreated and self.chunkSupport and self.size: #will be setted later by first chunk

                if not resume:
                    self.info.setSize(self.size)
                    self.info.createChunks(chunks)
                    self.info.save()

                chunks = self.info.getCount()

                init.range = self.info.getChunkRange(0)

                for i in range(1, chunks):
                    c = HTTPChunk(i, self, self.info.getChunkRange(i), resume)

                    handle = c.getHandle()
                    if handle:
                        self.chunks.append(c)
                        self.m.add_handle(handle)
                    else:
                        #close immediatly
                        c.close()


                chunksCreated = True


            while 1:
                ret, num_handles = self.m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            while 1:
                num_q, ok_list, err_list = self.m.info_read()
                for c in ok_list:
                    chunksDone += 1
                for c in err_list:
                    curl, errno, msg = c
                    #test if chunk was finished, otherwise raise the exception
                    if errno != 23 or "0 !=" not in msg:
                        raise pycurl.error(errno, msg)

                    #@TODO KeyBoardInterrupts are seen as finished chunks,
                    #but normally not handled to this process, only in the testcase
                    
                    chunksDone += 1
                if not num_q:
                    break

            if chunksDone == len(self.chunks):
                break #all chunks loaded

            # calc speed once per second
            t = time()
            if self.lastChecked + 1 < t:
                diff = [c.arrived - (self.lastArrived[i] if len(self.lastArrived) > i else 0) for i, c in
                        enumerate(self.chunks)]

                self.lastSpeeds[1] = self.lastSpeeds[0]
                self.lastSpeeds[0] = self.speeds
                self.speeds = [float(a) / (t - self.lastChecked) for a in diff]
                self.lastArrived = [c.arrived for c in self.chunks]
                self.lastChecked = t
                self.updateProgress()

            if self.abort:
                raise Abort()

            sleep(0.003) #supress busy waiting - limits dl speed to  (1 / x) * buffersize
            self.m.select(1)

        failed = False
        for chunk in self.chunks:
            try:
                chunk.verifyHeader()
            except BadHeader, e:
                failed = e.code
                remove(self.info.getChunkName(chunk.id))

            chunk.fp.flush()
            fsync(chunk.fp) #make sure everything was written to disk
            chunk.fp.close() #needs to be closed, or merging chunks will fail

        if failed: raise BadHeader(failed)

        self._copyChunks()
    
    def updateProgress(self):
        if self.progressNotify:
            self.progressNotify(self.percent)
    
    def close(self):
        """ cleanup """
        for chunk in self.chunks:
            chunk.close()
            self.m.remove_handle(chunk.c)

        self.chunks = []
        if hasattr(self, "m"):
            self.m.close()
            del self.m
        if hasattr(self, "cj"):
            del self.cj
        if hasattr(self, "info"):
            del self.info

if __name__ == "__main__":
    url = "http://speedtest.netcologne.de/test_100mb.bin"

    from Bucket import Bucket

    bucket = Bucket()
    bucket.setRate(200 * 1024)
    bucket = None

    print "starting"

    dwnld = HTTPDownload(url, "test_100mb.bin", bucket=bucket)
    dwnld.download(chunks=3, resume=True)
