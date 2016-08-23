# -*- coding: utf-8 -*-

import os
import re
import select
import socket
import struct
import time

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import exists, fsjoin


class XDCC(Hoster):
    __name__    = "XDCC"
    __type__    = "hoster"
    __version__ = "0.42"
    __status__  = "testing"

    __pattern__ = r'xdcc://(?P<SERVER>.*?)/#?(?P<CHAN>.*?)/(?P<BOT>.*?)/#?(?P<PACK>\d+)/?'
    __config__  = [("nick",         "str", "Nickname",           "pyload"               ),
                   ("ident",        "str", "Ident",              "pyloadident"          ),
                   ("realname",     "str", "Realname",           "pyloadreal"           ),
                   ("ctcp_version", "str","CTCP version string", "pyLoad! IRC Interface")]

    __description__ = """Download from IRC XDCC bot"""
    __license__     = "GPLv3"
    __authors__     = [("jeix",      "jeix@hasnomail.com"        ),
                       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    def setup(self):
        self.timeout = 30
        self.multiDL = False


    def process(self, pyfile):
        #: Change request type
        self.req = self.pyload.requestFactory.getRequest(self.classname, type="XDCC")

        for _i in xrange(0, 3):
            try:
                nmn = self.do_download(pyfile.url)
                self.log_info("Download of %s finished." % nmn)
                return

            except socket.error, e:
                if hasattr(e, "errno") and e.errno is not None:
                    err_no = e.errno

                    if err_no in (10054, 10061):
                        self.log_warning("Server blocked our ip, retry in 5 min")
                        self.wait(300)
                        continue

                    else:
                        self.log_error(_("Failed due to socket errors. Code: %s") % err_no)
                        self.fail(_("Failed due to socket errors. Code: %s") % err_no)

                else:
                    err_msg = e.args[0]
                    self.log_error(_("Failed due to socket errors: '%s'") % err_msg)
                    self.fail(_("Failed due to socket errors: '%s'") % err_msg)

        self.log_error(_("Server blocked our ip, retry again later manually"))
        self.fail(_("Server blocked our ip, retry again later manually"))


    def do_download(self, url):
        self.pyfile.setStatus("waiting")

        server, chan, bot, pack = re.match(self.__pattern__, url).groups()

        nick          = self.config.get('nick')
        ident         = self.config.get('ident')
        realname      = self.config.get('realname')
        ctcp_version  = self.config.get('ctcp_version')

        temp = server.split(':')
        ln = len(temp)
        if ln == 2:
            host, port = temp

        elif ln == 1:
            host, port = temp[0], 6667

        else:
            self.fail(_("Invalid hostname for IRC Server: %s") % server)

        #######################
        #: CONNECT TO IRC AND IDLE FOR REAL LINK
        dl_time = time.time()

        sock = socket.socket()

        self.log_info(_("Connecting to: %s:%s") % (host, port))
        sock.connect((host, int(port)))
        if nick == "pyload":
            nick = "pyload-%d" % (time.time() % 1000)  #: last 3 digits

        sock.send("NICK %s\r\n" % nick)
        sock.send("USER %s %s bla :%s\r\n" % (ident, host, realname))

        self.log_info(_("Connect success."))

        self.wait(5) # Wait for logon to complete

        sock.send("JOIN #%s\r\n" % chan)
        sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))

        #: IRC recv loop
        readbuffer = ""
        retry = None
        m = None
        while m is None:
            if retry:
                if time.time() > retry:
                    retry = None
                    dl_time = time.time()
                    sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))

            else:
                if (dl_time + self.timeout) < time.time():  #@TODO: add in config
                    sock.send("QUIT :byebye\r\n")
                    sock.close()
                    self.log_error(_("XDCC Bot did not answer"))
                    self.fail(_("XDCC Bot did not answer"))

            fdset = select.select([sock], [], [], 0)
            if sock not in fdset[0]:
                continue

            readbuffer += sock.recv(1024)
            lines = readbuffer.split("\n")
            readbuffer = lines.pop()

            for line in lines:
                # if self.pyload.debug:
                    # self.log_debug("*> " + decode(line))
                line = line.rstrip()
                first = line.split()

                if first[0] == "PING":
                    sock.send("PONG %s\r\n" % first[1])

                if first[0] == "ERROR":
                    self.fail(_("IRC-Error: %s") % line)

                msg = line.split(None, 3)
                if len(msg) != 4:
                    continue

                msg = {'origin': msg[0][1:],
                       'action': msg[1],
                       'target': msg[2],
                       'text'  : msg[3][1:]}

                if msg['target'][0:len(nick)] == nick and msg['action'] == "PRIVMSG":
                    if msg['text'] == "\x01VERSION\x01":
                        self.log_debug(_("Sending CTCP VERSION"))
                        sock.send("NOTICE %s :%s\r\n" % (msg['origin'], ctcp_version))

                    elif msg['text'] == "\x01TIME\x01":
                        self.log_debug(_("Sending CTCP TIME"))
                        sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))

                    elif msg['text'] == "\x01LAG\x01":
                        pass  #: don't know how to answer

                if msg['origin'][0:len(bot)] != bot\
                        or msg['target'][0:len(nick)] != nick\
                        or msg['action'] not in ("PRIVMSG", "NOTICE"):
                    continue

                self.log_debug(_("PrivMsg: <%s> - %s" % (msg['origin'], msg['text'])))

                if "You already requested that pack" in msg['text']:
                    retry = time.time() + 300

                elif "you must be on a known channel to request a pack" in msg['text']:
                    self.log_error(_("Invalid channel"))
                    self.fail(_("Invalid channel"))

                m = re.match('\x01DCC SEND (?P<NAME>.*?) (?P<IP>\d+) (?P<PORT>\d+)(?: (?P<SIZE>\d+))?\x01', msg['text'])

        #: Get connection data
        ip        = socket.inet_ntoa(struct.pack('!I', int(m.group('IP'))))
        port      = int(m.group('PORT'))
        file_name = m.group('NAME')
        if m.group('SIZE'):
            self.req.filesize = long(m.group('SIZE'))

        self.pyfile.name = file_name

        dl_folder = fsjoin(self.pyload.config.get('general', 'download_folder'),
                           self.pyfile.package().folder if self.pyload.config.get("general",
                                                                                  "folder_per_package") else "")
        dl_file = fsjoin(dl_folder, file_name)

        if not exists(dl_folder):
            os.makedirs(dl_folder)

        self.set_permissions(dl_folder)

        self.log_info(_("Downloading %s from %s:%d") % (file_name, ip, port))

        self.pyfile.setStatus("downloading")

        newname = self.req.download(ip, port, dl_file, sock, self.pyfile.setProgress)
        if newname and newname != dl_file:
            self.log_info(_("%(name)s saved as %(newname)s") % {'name': self.pyfile.name, 'newname': newname})
            dl_file = newname

        #: kill IRC socket
        #: sock.send("QUIT :byebye\r\n")
        sock.close()

        self.last_download = dl_file
        return self.last_download
