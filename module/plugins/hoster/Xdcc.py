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

from os.path import join
from os.path import exists
from os import makedirs
import re
import sys
import time
import socket, struct
from select import select
from module.utils import save_join

from module.plugins.Hoster import Hoster


class Xdcc(Hoster):
    __name__ = "Xdcc"
    __version__ = "0.3"
    __pattern__ = r'xdcc://.*?(/#?.*?)?/.*?/#?\d+/?' # xdcc://irc.Abjects.net/#channel/[XDCC]|Shit/#0004/
    __type__ = "hoster"
    __config__ = [
                    ("nick", "str", "Nickname", "pyload"),
                    ("ident", "str", "Ident", "pyloadident"),
                    ("realname", "str", "Realname", "pyloadreal")
                 ]
    __description__ = """A Plugin that allows you to download from an IRC XDCC bot"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.com")
    
    def setup(self):
        self.debug   = 0  #0,1,2
        self.timeout = 30
        self.multiDL = False
        
        
    
    def process(self, pyfile):
        # change request type
        self.req = pyfile.m.core.requestFactory.getRequest(self.__name__, type="XDCC")
    
        self.pyfile = pyfile
        for i in range(0,3):
            try:
                nmn = self.doDownload(pyfile.url)
                self.log.debug("%s: Download of %s finished." % (self.__name__, nmn))
                return
            except socket.error, e:
                if hasattr(e, "errno"):
                    errno = e.errno
                else:
                    errno = e.args[0]
                    
                if errno in (10054,):
                    self.log.debug("XDCC: Server blocked our ip, retry in 5 min")
                    self.setWait(300)
                    self.wait()
                    continue                    

                self.fail("Failed due to socket errors. Code: %d" % errno)
                
        self.fail("Server blocked our ip, retry again later manually")


    def doDownload(self, url):
        self.pyfile.setStatus("waiting") # real link

        download_folder = self.config['general']['download_folder']
        location = join(download_folder, self.pyfile.package().folder.decode(sys.getfilesystemencoding()))
        if not exists(location): 
            makedirs(location)
            
        m = re.search(r'xdcc://(.*?)/#?(.*?)/(.*?)/#?(\d+)/?', url)
        server = m.group(1)
        chan   = m.group(2)
        bot    = m.group(3)
        pack   = m.group(4)
        nick   = self.getConf('nick')
        ident  = self.getConf('ident')
        real   = self.getConf('realname')
        
        temp = server.split(':')
        ln = len(temp)
        if ln == 2:
            host, port = temp
        elif ln == 1:
            host, port = temp[0], 6667
        else:
            self.fail("Invalid hostname for IRC Server (%s)" % server)
        
        
        #######################
        # CONNECT TO IRC AND IDLE FOR REAL LINK
        dl_time = time.time()
        
        sock = socket.socket()
        sock.connect((host, int(port)))
        if nick == "pyload":
            nick = "pyload-%d" % (time.time() % 1000) # last 3 digits
        sock.send("NICK %s\r\n" % nick)
        sock.send("USER %s %s bla :%s\r\n" % (ident, host, real))
        time.sleep(3)
        sock.send("JOIN #%s\r\n" % chan)
        sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))
        
        # IRC recv loop
        readbuffer = ""
        done = False
        retry = None
        m = None
        while True:

            # done is set if we got our real link
            if done:
                break
        
            if retry:
                if time.time() > retry:
                    retry = None
                    dl_time = time.time()
                    sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))

            else:
                if (dl_time + self.timeout) < time.time(): # todo: add in config
                    sock.send("QUIT :byebye\r\n")
                    sock.close()
                    self.fail("XDCC Bot did not answer")


            fdset = select([sock], [], [], 0)
            if sock not in fdset[0]:
                continue
                
            readbuffer += sock.recv(1024)
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                if self.debug is 2: print "*> " + unicode(line, errors='ignore')
                line  = line.rstrip()
                first = line.split()

                if first[0] == "PING":
                    sock.send("PONG %s\r\n" % first[1])
                    
                if first[0] == "ERROR":
                    self.fail("IRC-Error: %s" % line)
                    
                msg = line.split(None, 3)
                if len(msg) != 4:
                    continue
                    
                msg = { \
                    "origin":msg[0][1:], \
                    "action":msg[1], \
                    "target":msg[2], \
                    "text"  :msg[3][1:] \
                }


                if nick == msg["target"][0:len(nick)] and "PRIVMSG" == msg["action"]:
                    if msg["text"] == "\x01VERSION\x01":
                        self.log.debug("XDCC: Sending CTCP VERSION.")
                        sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
                    elif msg["text"] == "\x01TIME\x01":
                        self.log.debug("Sending CTCP TIME.")
                        sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))
                    elif msg["text"] == "\x01LAG\x01":
                        pass # don't know how to answer
                
                if not (bot == msg["origin"][0:len(bot)] 
                    and nick == msg["target"][0:len(nick)] 
                    and msg["action"] in ("PRIVMSG", "NOTICE")):
                    continue
                    
                if self.debug is 1:
                    print "%s: %s" % (msg["origin"], msg["text"])
                    
                if "You already requested that pack" in msg["text"]:
                    retry = time.time() + 300
                    
                if "you must be on a known channel to request a pack" in msg["text"]:
                    self.fail("Wrong channel")
            
                m = re.match('\x01DCC SEND (.*?) (\d+) (\d+)(?: (\d+))?\x01', msg["text"])
                if m:
                    done = True
                
        # get connection data
        ip       = socket.inet_ntoa(struct.pack('L', socket.ntohl(int(m.group(2)))))
        port     = int(m.group(3))        
        packname = m.group(1)
        
        if len(m.groups()) > 3:
            self.req.filesize = int(m.group(4))
            
        self.pyfile.name = packname
        filename = save_join(location, packname)
        self.log.info("XDCC: Downloading %s from %s:%d" % (packname, ip, port))

        self.pyfile.setStatus("downloading")
        newname = self.req.download(ip, port, filename, sock, self.pyfile.setProgress)
        if newname and newname != filename:
            self.log.info("%(name)s saved as %(newname)s" % {"name": self.pyfile.name, "newname": newname})
            filename = newname
        
        # kill IRC socket
        # sock.send("QUIT :byebye\r\n")
        sock.close()

        self.lastDownload = filename
        return self.lastDownload
        
