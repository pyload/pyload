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

from HTTPBase import HTTPBase
from urllib2 import HTTPError
from threading import Lock
from helper import *
from time import sleep
from traceback import print_exc

class HTTPChunk(HTTPBase):
    def __init__(self, url, fh, get={}, post={}, referer=None, cookies=True, customHeaders={}, range=None, bucket=None, interface=None, proxies={}):
        HTTPBase.__init__(self, interface=interface, proxies=proxies)
        
        self.url = url
        self.bucket = bucket
        self.range = range
        self.noRangeHeader = False
        self.fh = fh
        
        self.get = get
        self.post = post
        self.referer = referer
        self.cookies = cookies
        self.customHeaders = customHeaders
        
        self.deferred = Deferred()
        
        self.abort = False
        self.finished = False
        
        self.arrived = 0
        
        self.startTime = None
        self.endTime = None
        
        self.speed = 0 #byte/sec
        self.speedCalcTime = None
        self.speedCalcLen = 0
        
        self.bufferSize = 16*1024 #tune if performance is poor
        self.resp = None
    
    def getSpeed(self):
        return self.speed
    
    @threaded
    def _download(self, resp):
        self.arrived = 0
        self.lastSpeed = self.startTime = inttime()
        
        if self.noRangeHeader and not self.range[0] == 0:
            self.deferred.error("range starts not at 0")
        
        running = True
        while running:
            if self.abort:
                break
            count = self.bufferSize
            if self.noRangeHeader:
                count = min(count, self.range[1] - self.arrived)
            if self.bucket:
                allow = self.bucket.consume(count)
                if not allow:
                    sleep(0.01)
                    continue
            
            try:
                data = resp.read(count)
            except:
                self.deferred.error("timeout")
                break
            
            if self.speedCalcTime < inttime():
                self.speed = self.speedCalcLen
                self.speedCalcTime = inttime()
                self.speedCalcLen = 0
            size = len(data)
            
            self.arrived += size
            self.speedCalcLen += size

            if self.noRangeHeader and self.arrived == self.range[1]:
                running = False

            if data:
                self.fh.write(data)
            else:
                break
        
        self.speed = 0
        self.endTime = inttime()
        self.finished = True
        self.fh.close()
        
        if self.abort:
            self.deferred.error("abort")
        elif self.size == self.arrived:
            self.deferred.callback(resp)
        else:
            self.deferred.error("wrong content lenght")
    
    def getEncoding(self):
        try:
            if self.resp.info()["Content-Encoding"] in ("gzip", "deflate"):
                return self.resp.info()["Content-Encoding"]
        except:
            pass
        return "plain"
    
    def download(self):
        if self.range:
            self.customHeaders["Range"] = "bytes=%i-%i" % self.range
        try:
            print "req"
            resp = self.getResponse(self.url, self.get, self.post, self.referer, self.cookies, self.customHeaders)
            self.resp = resp
        except HTTPError, e:
            print_exc()
            self.deferred.error(e)
            return self.deferred
        
        if (self.range and resp.getcode() == 206) or (not self.range and resp.getcode() == 200):
            self._download(resp)
        else:
            self.deferred.error(resp.getcode(), resp)
        return self.deferred

if __name__ == "__main__":
    import sys
    from Bucket import Bucket
    bucket = Bucket()
    bucket.setRate(200*1000)
    #bucket = None
    
    url = "http://speedtest.netcologne.de/test_100mb.bin"
    
    finished = 0
    def err(*a, **b):
        print a, b
    def callb(*a, **b):
        global finished
        finished += 1
        print a, b
    
    print "starting"
    
    conns = 4
    
    chunks = []
    for a in range(conns):
        fh = open("file.part%d" % a, "wb")
        chunk = HTTPChunk(url, fh, bucket=bucket, range=(a*5*1024*1024, (a+1)*5*1024*1024))
        print "fireing chunk #%d" % a
        d = chunk.download()
        d.addCallback(callb)
        d.addErrback(err)
        chunks.append(chunk)
    
    try:
        while True:
            aspeed = 0
            for a, chunk in enumerate(chunks):
                if not chunk.finished:
                    print "#%d" % a, chunk.getSpeed()/1024, "kb/s"
                else:
                    print "#%d" % a, "finished"
                aspeed += chunk.getSpeed()
            print "sum", aspeed/1024
            if finished == conns:
                print "- finished"
                break
            sleep(1)
    except KeyboardInterrupt:
        for chunk in chunks:
            chunk.abort = True
        sys.exit()
