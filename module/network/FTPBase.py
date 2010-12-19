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

from ftplib import FTP

import socket
import socks

from os.path import getsize
from urlparse import urlparse
from urllib2 import _parse_proxy

from helper import *

class FTPBase(FTP):
    sourceAddress = ('', 0)
    
    def setSourceAddress(self, host):
        self.sourceAddress = (host, 0)
    
    def connect(self, host='', port=0, timeout=30, proxies={}):
        if host != '':
            self.host = host
        if port > 0:
            self.port = port
        self.timeout = timeout
        
        proxytype = None
        proxy = None
        if proxies.has_key("socks5"):
            proxytype = socks.PROXY_TYPE_SOCKS5
            proxy = proxies["socks5"]
        elif proxies.has_key("socks4"):
            proxytype = socks.PROXY_TYPE_SOCKS4
            proxy = proxies["socks4"]
        if proxytype:
            self.sock = socks.socksocket()
            t = _parse_proxy(proxy)
            self.sock.setproxy(proxytype, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        else:
            self.sock = socket.socket()
        self.sock.settimeout(self.timeout)
        self.sock.bind(self.sourceAddress)
        self.sock.connect((self.host, self.port))
        self.af = self.sock.family
        self.file = self.sock.makefile('rb')
        self.welcome = self.getresp()
        return self.welcome

class FTPDownload():
    def __init__(self, url, filename, interface=None, bucket=None, proxies={}):
        self.url = url
        self.filename = filename
        
        self.bucket = bucket
        self.interface = interface
        self.proxies = proxies
        
        self.deferred = Deferred()
        
        self.finished = False
        self.size = None
        
        self.speed = 0
        
        self.abort = False
        
        self.arrived = 0
        
        self.startTime = None
        self.endTime = None
        
        self.speed = 0 #byte/sec
        self.speedCalcTime = None
        self.speedCalcLen = 0
        
        self.bufferSize = 16*1024 #tune if performance is poor
        
        self.ftp = FTPBase()
        self.fh = None
    
    @threaded
    def _download(self, offset):
        remotename = self.url.split("/")[-1]
        cmd = "RETR %s" % remotename
        
        self.startTime = inttime()
        self.arrived = offset
        conn, size = self.ftp.ntransfercmd(cmd, None if offset == 0 else offset) #explicit None
        if size:
            self.size = size + offset
        while True:
            if self.abort:
                self.ftp.abort()
                break
            count = self.bufferSize
            if self.bucket:
                count = self.bucket.add(count)
                if count == 0:
                    sleep(0.01)
                    continue
            
            try:
                data = conn.recv(count)
            except:
                self.deferred.error("timeout")
            
            if self.speedCalcTime < inttime():
                self.speed = self.speedCalcLen
                self.speedCalcTime = inttime()
                self.speedCalcLen = 0
            size = len(data)
            self.speedCalcLen += size
            self.arrived += size
            
            if not data:
                break
            
            self.fh.write(data)
        self.fh.close()
        conn.close()
        self.endTime = inttime()
        if not self.abort:
            print self.ftp.voidresp() #debug
        
            self.ftp.quit()
        if self.abort:
            self.deferred.error("abort")
        elif self.size is None or self.size == self.arrived:
            self.deferred.callback()
        else:
            self.deferred.error("wrong content lenght")
    
    def download(self, resume=False):
        self.fh = open("%s.part" % self.filename, "ab" if resume else "wb")
        offset = 0
        if resume:
            offset = getsize("%s.part" % self.filename)
        
        up = urlparse(self.url)
        
        self.ftp.connect(up.hostname, up.port if up.port else 21, proxies=self.proxies)
        self.ftp.login(up.username, up.password)
        self.ftp.cwd("/".join(up.path.split("/")[:-1]))
        self.ftp.voidcmd('TYPE I')
        self.size = self.ftp.size(self.url.split("/")[-1])
        
        self._download(offset)
        return self.deferred

if __name__ == "__main__":
    import sys
    from Bucket import Bucket
    bucket = Bucket()
    bucket.setRate(200*1000)
    #bucket = None
    
    url = "ftp://mirror.sov.uk.goscomb.net/ubuntu-releases/maverick/ubuntu-10.10-desktop-i386.iso"
    
    finished = False
    def err(*a, **b):
        print a, b
    def callb(*a, **b):
        global finished
        finished = True
        print a, b
    
    print "starting"
    
    dwnld = FTPDownload(url, "ubuntu_ftp.iso")
    d = dwnld.download(resume=True)
    d.addCallback(callb)
    d.addErrback(err)
    
    try:
        while True:
            if not dwnld.finished:
                print dwnld.speed/1024, "kb/s", "size", dwnld.arrived, "/", dwnld.size#, int(float(dwnld.arrived)/dwnld.size*100), "%"
            if finished:
                print "- finished"
                break
            sleep(1)
    except KeyboardInterrupt:
        dwnld.abort = True
        sys.exit()
