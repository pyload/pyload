# -*- coding: utf-8 -*-

import re
import socket
import struct
import sys
import time

from os import makedirs
from os.path import exists, join
from select import select

from module.plugins.Hoster import Hoster
from module.utils import safe_join


class Xdcc(Hoster):
    __name__ = "Xdcc"
    __type__ = "hoster"
    __version__ = "0.32"

    __config__ = [("nick", "str", "Nickname", "pyload"),
                  ("ident", "str", "Ident", "pyloadident"),
                  ("realname", "str", "Realname", "pyloadreal")]

    __description__ = """Download from IRC XDCC bot"""
    __author_name__ = "jeix"
    __author_mail__ = "jeix@hasnomail.com"


    def setup(self):
        self.debug = 0  # 0,1,2
        self.timeout = 30
        self.multiDL = False

    def process(self, pyfile):
        # change request type
        self.req = pyfile.m.core.requestFactory.getRequest(self.__name__, type="XDCC")

        self.pyfile = pyfile
        for _ in xrange(0, 3):
            try:
                nmn = self.doDownload(pyfile.url)
                self.logDebug("%s: Download of %s finished." % (self.__name__, nmn))
                return
            except socket.error, e:
                if hasattr(e, "errno"):
                    errno = e.errno
                else:
                    errno = e.args[0]

                if errno == 10054:
                    self.logDebug("XDCC: Server blocked our ip, retry in 5 min")
                    self.setWait(300)
                    self.wait()
                    continue

                self.fail("Failed due to socket errors. Code: %d" % errno)

        self.fail("Server blocked our ip, retry again later manually")

    def doDownload(self, url):
        self.pyfile.setStatus("waiting")  # real link

        m = re.match(r'xdcc://(.*?)/#?(.*?)/(.*?)/#?(\d+)/?', url)
        server = m.group(1)
        chan = m.group(2)
        bot = m.group(3)
        pack = m.group(4)
        nick = self.getConfig('nick')
        ident = self.getConfig('ident')
        real = self.getConfig('realname')

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
            nick = "pyload-%d" % (time.time() % 1000)  # last 3 digits
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
                if (dl_time + self.timeout) < time.time():  # todo: add in config
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
                if self.debug is 2:
                    print "*> " + unicode(line, errors='ignore')
                line = line.rstrip()
                first = line.split()

                if first[0] == "PING":
                    sock.send("PONG %s\r\n" % first[1])

                if first[0] == "ERROR":
                    self.fail("IRC-Error: %s" % line)

                msg = line.split(None, 3)
                if len(msg) != 4:
                    continue

                msg = {
                    "origin": msg[0][1:],
                    "action": msg[1],
                    "target": msg[2],
                    "text": msg[3][1:]
                }

                if nick == msg['target'][0:len(nick)] and "PRIVMSG" == msg['action']:
                    if msg['text'] == "\x01VERSION\x01":
                        self.logDebug("XDCC: Sending CTCP VERSION.")
                        sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
                    elif msg['text'] == "\x01TIME\x01":
                        self.logDebug("Sending CTCP TIME.")
                        sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))
                    elif msg['text'] == "\x01LAG\x01":
                        pass  # don't know how to answer

                if not (bot == msg['origin'][0:len(bot)]
                        and nick == msg['target'][0:len(nick)]
                        and msg['action'] in ("PRIVMSG", "NOTICE")):
                    continue

                if self.debug is 1:
                    print "%s: %s" % (msg['origin'], msg['text'])

                if "You already requested that pack" in msg['text']:
                    retry = time.time() + 300

                if "you must be on a known channel to request a pack" in msg['text']:
                    self.fail("Wrong channel")

                m = re.match('\x01DCC SEND (.*?) (\d+) (\d+)(?: (\d+))?\x01', msg['text'])
                if m:
                    done = True

        # get connection data
        ip = socket.inet_ntoa(struct.pack('L', socket.ntohl(int(m.group(2)))))
        port = int(m.group(3))
        packname = m.group(1)

        if len(m.groups()) > 3:
            self.req.filesize = int(m.group(4))

        self.pyfile.name = packname

        download_folder = self.config['general']['download_folder']
        filename = safe_join(download_folder, packname)

        self.logInfo("XDCC: Downloading %s from %s:%d" % (packname, ip, port))

        self.pyfile.setStatus("downloading")
        newname = self.req.download(ip, port, filename, sock, self.pyfile.setProgress)
        if newname and newname != filename:
            self.logInfo("%(name)s saved as %(newname)s" % {"name": self.pyfile.name, "newname": newname})
            filename = newname

        # kill IRC socket
        # sock.send("QUIT :byebye\r\n")
        sock.close()

        self.lastDownload = filename
        return self.lastDownload
