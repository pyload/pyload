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

import socket
import socks
import re

from os.path import getsize
from urlparse import urlparse
from urllib2 import _parse_proxy

from helper import *
from time import sleep

import struct
from select import select

class XDCCError(Exception):
    pass

class XDCCDownload():
    def __init__(self, server, port, channel, bot, pack, nick, ident, real, filename, timeout=30, bucket=None, interface=None, proxies={}):
        self.server = server
        self.port = port
        self.channel = channel
        self.bot = bot
        self.pack = pack
        self.nick = nick
        self.ident = ident
        self.real = real
        self.filename = filename
        self.bucket = bucket
        self.interface = interface
        self.proxies = proxies
        self.timeout = timeout
        self.debug = 2
        
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
        
        self.fh = None
    
    def createSocket(self):
        proxytype = None
        proxy = None
        if self.proxies.has_key("socks5"):
            proxytype = socks.PROXY_TYPE_SOCKS5
            proxy = self.proxies["socks5"]
        elif self.proxies.has_key("socks4"):
            proxytype = socks.PROXY_TYPE_SOCKS4
            proxy = self.proxies["socks4"]
        if proxytype:
            sock = socks.socksocket()
            t = _parse_proxy(proxy)
            sock.setproxy(proxytype, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        else:
            sock = socket.socket()
        return sock
    
    def _download(self, ip, port):
        startTime = inttime()
        
        dccsock = self.createSocket()
        
        dccsock.settimeout(self.timeout)
        dccsock.bind(self.sourceAddress)
        dccsock.connect((ip, port))
        
        # recv loop for dcc socket
        while True:
            if self.abort:
                break
            count = 4096
            if self.bucket:
                count = self.bucket.add(count)
                if count < 4096:
                    sleep(0.01)
                    continue
            
            try:
                data = dccsock.recv(count)
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
            
            # acknowledge data by sending number of recceived bytes
            dccsock.send(struct.pack('!I', self.arrived))
        
        dccsock.close()
        self.fh.close()
        
        self.endTime = inttime()
        if self.abort:
            self.deferred.error("abort")
        elif self.size is None or self.size == self.arrived:
            self.deferred.callback()
        else:
            self.deferred.error("wrong content lenght")
    
    def download(self):
        self.fh = open(self.filename, "wb")
        
        def debug(s):
            print "XDCC:", s
        
        sock = self.createSocket()
        print self.server, self.port
        sock.connect((self.server, int(self.port)))
        _realsend = sock.send
        def send(s):
            if self.debug == 2:
                print s
            _realsend(s)
        sock.send = send
        
        sock.send("NICK %s\r\n" % self.nick)
        sock.send("USER %s %s bla :%s\r\n" % (self.ident, self.server, self.real))
        sleep(3)
        sock.send("JOIN #%s\r\n" % self.channel)
        sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (self.bot, self.pack))
        
        # IRC recv loop
        readbuffer = ""
        dlTime = inttime()
        done = False
        retry = None
        while True:
            # done is set if we got our real link
            if done: break
            
            if retry:
                if inttime() > retry:
                    retry = None
                    dlTime = inttime()
                    sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (self.bot, self.pack))

            else:
                if (dlTime + self.timeout) < inttime():
                    sock.send("QUIT :byebye\r\n")
                    sock.close()
                    raise XDCCError("XDCC Bot did not answer")


            fdset = select([sock], [], [], 0)
            if sock not in fdset[0]:
                continue
                
            readbuffer += sock.recv(1024)
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                if self.debug is 2: print "*> " + line
                line  = line.rstrip()
                first = line.split()

                if(first[0] == "PING"):
                    sock.send("PONG %s\r\n" % first[1])
                    
                if first[0] == "ERROR":
                    raise XDCCError("IRC-Error: %s" % line)
                    
                msg = line.split(None, 3)
                if len(msg) != 4:
                    continue
                    
                msg = { \
                    "origin":msg[0][1:], \
                    "action":msg[1], \
                    "target":msg[2], \
                    "text"  :msg[3][1:] \
                }


                if self.nick == msg["target"][0:len(self.nick)] and "PRIVMSG" == msg["action"]:
                    if msg["text"] == "\x01VERSION\x01":
                        debug("XDCC: Sending CTCP VERSION.")
                        sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
                    elif msg["text"] == "\x01TIME\x01":
                        debug("Sending CTCP TIME.")
                        sock.send("NOTICE %s :%d\r\n" % (msg['origin'], inttime()))
                    elif msg["text"] == "\x01LAG\x01":
                        pass # don't know how to answer
                
                if not (self.bot == msg["origin"][0:len(self.bot)] 
                    and self.nick == msg["target"][0:len(self.nick)] 
                    and msg["action"] in ("PRIVMSG", "NOTICE")):
                    continue
                    
                if self.debug is 1:
                    print "%s: %s" % (msg["origin"], msg["text"])
                    
                if "You already requested that pack" in msg["text"]:
                    retry = inttime() + 300
                    
                if "you must be on a known channel to request a pack" in msg["text"]:
                    raise XDCCError("Wrong channel")
            
                m = re.match('\x01DCC SEND (.*?) (\d+) (\d+)(?: (\d+))?\x01', msg["text"])
                if m != None:
                    done = True
                
        # get connection data
        ip = socket.inet_ntoa(struct.pack('L', socket.ntohl(int(m.group(2)))))
        port = int(m.group(3))
        self.realfilename = m.group(1)
        
        if len(m.groups()) > 3:
            self.size = int(m.group(4))
        
        debug("XDCC: Downloading %s from %s:%d" % (packname, ip, port))
        
        self._download(ip, port)
        return self.deferred

if __name__ == "__main__":
    import sys
    from Bucket import Bucket
    bucket = Bucket()
    #bucket.setRate(200*1000)
    bucket = None
    
    finished = False
    def err(*a, **b):
        print a, b
    def callb(*a, **b):
        global finished
        finished = True
        print a, b
    
    print "starting"
    dwnld = XDCCDownload("<server>", 6667, "<chan>", "<bot>", "<pack>", "<nick>", "<ident>", "<real>", "<filename>")
    d = dwnld.download()
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
