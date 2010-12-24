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
    
    @author: mkaay
"""

from HTTPChunk import HTTPChunk
from helper import *
from os.path import exists, getsize
from os import remove
#from shutil import move, copyfileobj
from zlib import decompressobj, MAX_WBITS

from cookielib import CookieJar

class WrongFormat(Exception):
    pass

class ChunkInfo():
    def __init__(self, name):
        self.name = name
        self.size = None
        self.loaded = False
        self.chunks = []
    
    def setSize(self, size):
        self.size = int(size)
    
    def addChunk(self, name, range, encoding):
        self.chunks.append((name, range, encoding))
    
    def clear(self):
        self.chunks = []
        self.loaded = False
    
    def save(self):
        fh = open("%s.chunks" % self.name, "w")
        fh.write("name:%s\n" % self.name)
        fh.write("size:%s\n" % self.size)
        for i, c in enumerate(self.chunks):
            fh.write("#%d:\n" % i)
            fh.write("\tname:%s\n" % c[0])
            fh.write("\tencoding:%s\n" % c[2])
            fh.write("\trange:%i-%i\n" % c[1])
    
    @staticmethod
    def load(name):
        if not exists("%s.chunks" % name):
            raise IOError()
        fh = open("%s.chunks" % name, "r")
        name = fh.readline()[:-1]
        size = fh.readline()[:-1]
        if name.startswith("name:") and size.startswith("size:"):
            name = name[5:]
            size = size[5:]
        else:
            raise WrongFormat()
        ci = ChunkInfo(name)
        ci.loaded = True
        ci.setSize(size)
        while True:
            if not fh.readline(): #skip line
                break
            name = fh.readline()[1:-1]
            encoding = fh.readline()[1:-1]
            range = fh.readline()[1:-1]
            if name.startswith("name:") and encoding.startswith("encoding:") and range.startswith("range:"):
                name = name[5:]
                encoding = encoding[9:]
                range = range[6:].split("-")
            else:
                raise WrongFormat()
            
            ci.addChunk(name, (long(range[0]), long(range[1])), encoding)
        return ci
    
    def removeInfo(self):
        remove("%s.chunks" % self.name)
    
    def getCount(self):
        return len(self.chunks)
    
    def getChunkName(self, index):
        return self.chunks[index][0]
    
    def getChunkRange(self, index):
        return self.chunks[index][1]
        
    def getChunkEncoding(self, index):
        return self.chunks[index][2]

class WrappedHTTPDeferred(WrappedDeferred):
    pass
    
class HTTPDownload():
    def __init__(self, url, filename, get={}, post={}, referer=None, cookies=True, customHeaders={}, bucket=None, interface=None, proxies={}):
        self.url = url
        self.filename = filename
        self.interface = interface
        self.proxies = proxies
        
        self.get = get
        self.post = post
        
        self.referer = referer
        self.cookies = cookies
        
        self.customHeaders = customHeaders
        
        self.bucket = bucket
        
        self.deferred = Deferred()
        
        self.finished = False
        self._abort = False
        self.size = None
        
        self.cookieJar = CookieJar()
        
        self.chunks = []
        self.chunksDone = 0
        try:
            self.info = ChunkInfo.load(filename)
        except IOError:
            self.info = ChunkInfo(filename)
        self.noChunkSupport = False
    
    @property
    def arrived(self):
        arrived = 0
        try:
            for i in range(self.info.getCount()):
                arrived += getsize(self.info.getChunkName(i)) #ugly, but difficult to calc otherwise due chunk resume
        except OSError:
            arrived = self.size
        return arrived
    
    def setAbort(self, val):
        self._abort = val
        for chunk in self.chunks:
            chunk.abort = val
    
    def getAbort(self):
        return self._abort
    
    abort = property(getAbort, setAbort)
    
    def getSpeed(self):
        speed = 0
        for chunk in self.chunks:
            speed += chunk.getSpeed()
        return speed
    
    @property
    def speed(self):
        return self.getSpeed()
    
    def calcProgress(self, p):
        self.deferred.progress("percent", 100-int((self.size - self.arrived)/float(self.size)*100))
    
    def _chunkDone(self):
        self.chunksDone += 1
        print self.chunksDone, "/", len(self.chunks)
        if self.chunksDone == len(self.chunks):
            self._copyChunks()
    
    def _copyChunks(self):
        fo = open(self.filename, "wb") #out file
        for i in range(self.info.getCount()):
            encoding = self.info.getChunkEncoding(i)
            
            #decompress method, if any
            decompress = lambda data: data
            if encoding == "gzip":
                gz = decompressobj(16+MAX_WBITS)
                decompress = lambda data: gz.decompress(data)
            if encoding == "deflate":
                df = decompressobj(-MAX_WBITS)
                decompress = lambda data: df.decompress(data)
            
            #input file
            fname = "%s.chunk%d" % (self.filename, i)
            fi = open(fname, "rb")
            while True: #copy in chunks, consumes less memory
                data = fi.read(512*1024)
                if not data:
                    break
                fo.write(decompress(data)) #decompressing
            fi.close()
            remove(fname) #remove
        fo.close()
        self.info.removeInfo() #remove info file
        self.deferred.callback() #done, emit callbacks
    
    def _createChunk(self, fh, range=None):
        chunk = HTTPChunk(self.url, fh, get=self.get, post=self.post,
                          referer=self.referer, cookies=self.cookies,
                          customHeaders=self.customHeaders,
                          bucket=self.bucket, range=range,
                          interface=self.interface, proxies=self.proxies)
        chunk.cookieJar = self.cookieJar
        return chunk
    
    def _addChunk(self, chunk, d):
        self.chunks.append(chunk)
        d.addProgress("percent", self.calcProgress)
        d.addCallback(self._chunkDone)
        d.addErrback(lambda *args, **kwargs: self.setAbort(True))
        d.addErrback(self.deferred.error)
    
    def download(self, chunks=1, resume=False):
        self.chunksDone = 0
        if chunks > 0:
            #diffentent chunk count in info, resetting
            if self.info.loaded and not self.info.getCount() == chunks:
                self.info.clear()
            
            #if resuming, calculate range with offset
            crange = None
            if resume:
                if self.info.getCount() == chunks and exists("%s.chunk0" % (self.filename, )):
                    crange = self.info.getChunkRange(0)
                    crange = (crange[0]+getsize("%s.chunk0" % (self.filename, )), crange[1]-1)
            
            #if firstpart not done
            if crange is None or crange[1]-crange[0] > 0:
                fh = open("%s.chunk0" % (self.filename, ), "ab" if crange else "wb")
                
                chunk = self._createChunk(fh, range=crange)
                
                d = chunk.download() #start downloading
                self._addChunk(chunk, d)
                
                #no info file, need to calculate ranges
                if not self.info.loaded:
                    size = chunk.size #overall size
                    chunksize = size/chunks #chunk size
                    
                    chunk.range = (0, chunksize) #setting range for first part
                    chunk.noRangeHeader = True
                    chunk.size = chunksize #setting size for first chunk
                    
                    self.size = size #setting overall size
                    self.info.setSize(self.size) #saving overall size
                    self.info.addChunk("%s.chunk0" % (self.filename, ), chunk.range, chunk.getEncoding()) #add chunk to infofile
                    
                    lastchunk = size - chunksize*(chunks-1) #calculating size for last chunk
                self.firstchunk = chunk #remeber first chunk
            
            if self.info.loaded and not self.size:
                self.size = self.info.size #setting overall size
            
            for i in range(1, chunks): #other chunks
                cont = False
                if not self.info.loaded: #first time load
                    if i+1 == chunks: #last chunk?
                        rng = (i*chunksize, i*chunksize+lastchunk-1)
                    else:
                        rng = (i*chunksize, (i+1)*chunksize-1) #adjusting range
                else: #info available
                    rng = self.info.getChunkRange(i) #loading previous range
                    if resume and exists("%s.chunk%d" % (self.filename, i)): #continue chunk
                        rng = (rng[0]+getsize("%s.chunk%d" % (self.filename, i)), rng[1]) #adjusting offset
                        cont = True #set append mode
                
                if rng[1]-rng[0] <= 0: #chunk done
                    continue
                
                fh = open("%s.chunk%d" % (self.filename, i), "ab" if cont else "wb")
                chunk = self._createChunk(fh, range=rng)
                d = chunk.download() #try
                
                if not chunk.resp.getcode() == 206 and i == 1: #no range supported, tell first chunk to download everything
                    chunk.abort = True
                    self.noChunkSupport = True
                    self.firstchunk.size = self.size
                    self.firstchunk.range = None
                    self.info.clear() #clear info
                    self.info.addChunk("%s.chunk0" % (self.filename, ), (0, self.firstchunk.size), chunk.getEncoding()) #re-adding info with correct ranges
                    break
                
                self._addChunk(chunk, d)
                
                if not self.info.loaded: #adding info
                    self.info.addChunk("%s.chunk%d" % (self.filename, i), chunk.range, chunk.getEncoding())
            
            self.info.save() #saving info
            if not len(self.chunks):
                self._copyChunks()
            return WrappedHTTPDeferred(self, self.deferred)
        else:
            raise Exception("no chunks")

if __name__ == "__main__":
    import sys
    from Bucket import Bucket
    bucket = Bucket()
    bucket.setRate(200*1024)
    #bucket = None
    
    url = "http://speedtest.netcologne.de/test_100mb.bin"
    
    finished = False
    def err(*a, **b):
        print a, b
    def callb(*a, **b):
        global finished
        finished = True
        print a, b
    
    print "starting"
    
    dwnld = HTTPDownload(url, "test_100mb.bin", bucket=bucket)
    d = dwnld.download(chunks=5, resume=True)
    d.addCallback(callb)
    d.addErrback(err)
    
    try:
        while True:
            for a, chunk in enumerate(dwnld.chunks):
                if not chunk.finished:
                    print "#%d" % a, chunk.getSpeed()/1024, "kb/s", "size", int(float(chunk.arrived)/chunk.size*100), "%"
                else:
                    print "#%d" % a, "finished"
            print "sum", dwnld.speed/1024, dwnld.arrived, "/", dwnld.size, int(float(dwnld.arrived)/dwnld.size*100), "%"
            if finished:
                print "- finished"
                break
            sleep(1)
    except KeyboardInterrupt:
        dwnld.abort = True
        sys.exit()
