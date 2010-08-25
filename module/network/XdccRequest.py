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
    
    @author: spoob
    @author: RaNaN
    @author: mkaay
    @author: jeix
    @version: v0.4.0
"""

import time
import socket
from select import select
import re
from os import sep, rename, stat
from os.path import exists
import struct

class AbortDownload(Exception):
    pass
    
class IRCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class XDCCError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class XdccRequest:
    def __init__(self):

        self.dl_time = 0
        self.dl_finished = 0
        self.dl_size = 0
        self.dl_arrived = 0
        self.dl = False

        self.abort = False
       
        self.timeout = 20
        
        bufferBase = 1024
        bufferMulti = 4
        self.bufferSize = bufferBase*bufferMulti
        self.canContinue = False
        self.offset = 0
        
        self.dl_speed = 0.0
        self.averageSpeed = 0.0
        self.averageSpeeds = []
        self.averageSpeedTime = 0.0
        self.averageSpeedCount = 0.0
        
        self.speedLimitActive = False
        self.maxSpeed = 0
        self.isSlow = False
        
        # change this for connection information
        self.debug = False

    def set_timeout(self, timeout):
        self.timeout = int(timeout)
       
    def add_proxy(self, protocol, adress):
        # @TODO: pycurl proxy protocoll selection
        raise NotImplementedError

    # xdcc://irc.Abjects.net/[XDCC]|Shit/#0004/
    #nick, ident, realname, servers
    def download(self, bot, pack, path, nick, ident, realname, channel, host, port=6667):
        self.dl_time = time.time()
        self.dl = True
        
        self.chunkSize = 0
        self.chunkRead = 0
        self.subStartTime = 0
        self.maxChunkSize = 0
        
        def restLimit():
            subTime = time.time() - self.subStartTime
            if subTime <= 1:
                if self.speedLimitActive:
                    return self.maxChunkSize
                else:
                    return -1
            else:
                self.updateCurrentSpeed(float(self.chunkRead/1024) / subTime)
                
                self.subStartTime = time.time()
                self.chunkRead = 0
                if self.maxSpeed > 0:
                    self.maxChunkSize = self.maxSpeed
                else:
                    self.maxChunkSize = 0
                return 0

        def writefunc(in_chunkSize):
            chunkSize = in_chunkSize
            while chunkSize > restLimit() > -1:
                time.sleep(0.05)
            self.maxChunkSize -= chunkSize
            self.chunkRead += chunkSize
            self.dl_arrived += chunkSize
            
            
        # connect to IRC
        sock = socket.socket()
        sock.connect((host, port))
        if nick == "pyload":
            nick = "pyload-%d" % (time.time() % 1000) # last 3 digits
        sock.send("NICK %s\r\n" % nick)
        sock.send("USER %s %s bla :%s\r\n" % (ident, host, realname))
        sock.send("JOIN #%s\r\n" % channel)
        sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))
        
        # IRC recv loop
        readbuffer = ""
        while True:
            if self.abort:
                raise AbortDownload
        
            if self.dl_time + self.timeout < time.time():
                raise XDCCError("timeout, bot did not answer")
                
            #time.sleep(5) # cool down <- was a bullshit idea
            
            fdset = select([sock], [], [], 0)
            if sock not in fdset[0]:
                continue
                
            readbuffer += sock.recv(1024)
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                if self.debug: print "*> " + line
                line  = line.rstrip()
                first = line.split()

                if(first[0] == "PING"):
                    sock.send("PONG %s\r\n" % first[1])
                    
                if first[0] == "ERROR":
                    raise IRCError(line)
                    
                msg = line.split(None, 3)
                if len(msg) != 4:
                    continue
                    
                msg = { \
                    "origin":msg[0][1:], \
                    "action":msg[1], \
                    "target":msg[2], \
                    "text"  :msg[3][1:] \
                }
                

                if nick == msg["target"][0:len(nick)]\
                    and "PRIVMSG" == msg["action"]:
                    if msg["text"] == "\x01VERSION\x01":
                        if self.debug: print "Sending CTCP VERSION."
                        sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
                    elif msg["text"] == "\x01TIME\x01":
                        if self.debug: print "Sending CTCP TIME."
                        sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))
                    elif msg["text"] == "\x01LAG\x01":
                        pass # don't know how to answer
                
                if not (bot == msg["origin"][0:len(bot)] 
                    and nick == msg["target"][0:len(nick)] 
                    and "PRIVMSG" == msg["action"]):
                    continue
            
                m = re.match('\x01DCC SEND (.*?) (.*?) (.*?) (.*?)\x01', msg["text"])
                if m != None:
                    break
                
        # kill IRC socket
        sock.send("QUIT :byebye\r\n")
        sock.close()

        # connect to XDCC Bot
        dcc = socket.socket()                        
        ip  = socket.inet_ntoa(struct.pack('L', socket.ntohl(int(m.group(2)))))
        port = int(m.group(3))
        dcc.connect((ip, port))
        
        dcc_packname = m.group(1)
        if len(m.groups()) > 3:
            self.dl_size = int(m.group(4))
        dcc_packname = self.get_free_name(path + '\\' + dcc_packname)
        dcc_fpointer = open(dcc_packname + ".part", "wb")
        dcc_total = 0
        
        # recv loop for dcc socket
        while True:
            if self.abort:
                dcc.close()
                dcc_fpointer.close()
                raise AbortDownload
                
            fdset = select([dcc], [], [], 0)
            if dcc not in fdset[0]:
                continue
                
            # recv something
            recvbytes = dcc.recv(2**14)
                
            # connection closed and everything received -> reset variables
            if len(recvbytes) == 0:
                dcc.close()
                dcc_fpointer.close()
                break

            # status updates, speedmanaging, etc.
            writefunc(len(recvbytes))

            # add response to file
            dcc_fpointer.write(recvbytes)
            dcc_total += len(recvbytes)
            
            # acknowledge data by sending number of recceived bytes
            dcc.send(struct.pack('!I', dcc_total))
        ########################
        
        free_name = self.get_free_name(dcc_packname)
        rename(dcc_packname + ".part", free_name)
        
        self.dl = False
        self.dl_finished = time.time()

        return free_name
    
    def updateCurrentSpeed(self, speed):
        self.dl_speed = speed
        if self.averageSpeedTime + 10 < time.time():
            self.averageSpeeds = []
            self.averageSpeeds.append(self.averageSpeed)
            self.averageSpeeds.append(speed)
            self.averageSpeed = (speed + self.averageSpeed)/2
            self.averageSpeedTime = time.time()
            self.averageSpeedCount = 2
        else:
            self.averageSpeeds.append(speed)
            self.averageSpeedCount += 1
            allspeed = 0.0
            for s in self.averageSpeeds:
                allspeed += s
            self.averageSpeed = allspeed / self.averageSpeedCount
    
    def write_header(self, string):
        self.header += string

    def get_rep(self):
        value = self.rep.getvalue()
        self.rep.close()
        self.rep = StringIO()
        return value
    
    def get_header(self):
        h = self.header
        self.header = ""
        return h

    def get_speed(self):
        try:
            return self.dl_speed
        except:
            return 0

    def get_ETA(self):
        try:
            return (self.dl_size - self.dl_arrived) / (self.dl_arrived / (time.time() - self.dl_time))
        except:
            return 0

    def kB_left(self):
        return (self.dl_size - self.dl_arrived) / 1024
    
    def progress(self, dl_t, dl_d, up_t, up_d):
        if self.abort:
            return False
        self.dl_arrived = int(dl_d)
        self.dl_size = int(dl_t)

    def get_free_name(self, file_name):
        file_count = 0
        while exists(file_name):
            file_count += 1
            if "." in file_name:
                file_split = file_name.split(".")
                temp_name = "%s-%i.%s" % (".".join(file_split[:-1]), file_count, file_split[-1])
            else:
                temp_name = "%s-%i" % (file_name, file_count)
            if not exists(temp_name):
                file_name = temp_name
        return file_name
    
    def __del__(self):
        self.clean()
    
    def clean(self):
        try:
            pass
            # self.pycurl.close()
        except:
            pass

# def getURL(url):
    # """
        # currently used for update check
    # """
    # req = Request()
    # c = req.load(url)
    # req.pycurl.close()
    # return c

if __name__ == "__main__":
    import doctest
    doctest.testmod()
