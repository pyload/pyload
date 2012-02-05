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
    
    @author: jeix
"""

import socket
import re

from os import remove
from os.path import exists

from time import time

import struct
from select import select

from module.plugins.Plugin import Abort


class XDCCRequest():
    def __init__(self, timeout=30, proxies={}):
        
        self.proxies = proxies
        self.timeout = timeout
        
        self.filesize = 0
        self.recv = 0
        self.speed = 0
        
        self.abort = False

    
    def createSocket(self):
        # proxytype = None
        # proxy = None
        # if self.proxies.has_key("socks5"):
            # proxytype = socks.PROXY_TYPE_SOCKS5
            # proxy = self.proxies["socks5"]
        # elif self.proxies.has_key("socks4"):
            # proxytype = socks.PROXY_TYPE_SOCKS4
            # proxy = self.proxies["socks4"]
        # if proxytype:
            # sock = socks.socksocket()
            # t = _parse_proxy(proxy)
            # sock.setproxy(proxytype, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        # else:
            # sock = socket.socket()
        # return sock
        
        return socket.socket()
    
    def download(self, ip, port, filename, irc, progressNotify=None):

        ircbuffer = ""
        lastUpdate = time()
        cumRecvLen = 0
        
        dccsock = self.createSocket()
        
        dccsock.settimeout(self.timeout)
        dccsock.connect((ip, port))
        
        if exists(filename):
            i = 0
            nameParts = filename.rpartition(".")
            while True:
                newfilename = "%s-%d%s%s" % (nameParts[0], i, nameParts[1], nameParts[2])
                i += 1
                
                if not exists(newfilename):
                    filename = newfilename
                    break
        
        fh = open(filename, "wb")
        
        # recv loop for dcc socket
        while True:
            if self.abort:
                dccsock.close()
                fh.close()
                remove(filename)
                raise Abort()
            
            self._keepAlive(irc, ircbuffer)
            
            data = dccsock.recv(4096)
            dataLen = len(data)
            self.recv += dataLen
            
            cumRecvLen += dataLen
            
            now = time()
            timespan = now - lastUpdate
            if timespan > 1:            
                self.speed = cumRecvLen / timespan
                cumRecvLen = 0
                lastUpdate = now
                
                if progressNotify:
                    progressNotify(self.percent)
            
            
            if not data:
                break
            
            fh.write(data)
            
            # acknowledge data by sending number of recceived bytes
            dccsock.send(struct.pack('!I', self.recv))
        
        dccsock.close()
        fh.close()
        
        return filename
    
    def _keepAlive(self, sock, readbuffer):
        fdset = select([sock], [], [], 0)
        if sock not in fdset[0]:
            return
            
        readbuffer += sock.recv(1024)
        temp = readbuffer.split("\n")
        readbuffer = temp.pop()

        for line in temp:
            line  = line.rstrip()
            first = line.split()
            if first[0] == "PING":
                sock.send("PONG %s\r\n" % first[1])

    def abortDownloads(self):
        self.abort = True
    
    @property
    def size(self):
        return self.filesize

    @property
    def arrived(self):
        return self.recv

    @property
    def percent(self):
        if not self.filesize: return 0
        return (self.recv * 100) / self.filesize

    def close(self):
        pass
