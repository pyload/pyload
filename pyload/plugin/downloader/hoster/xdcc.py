# -*- coding: utf-8 -*-
#@author: jeix

from __future__ import print_function, unicode_literals
from __future__ import division
from __future__ import absolute_import

from builtins import int
from future import standard_library
standard_library.install_aliases()
import os
import re
import socket
import struct
import sys
import time
from builtins import range
from contextlib import closing
from select import select

from pyload.plugin.downloader.hoster import Hoster
from pyload.utils import format
from pyload.utils.path import makedirs


class Xdcc(Hoster):
    __name__ = "Xdcc"
    __version__ = "0.32"
    # xdcc://irc.Abjects.net/#channel/[XDCC]|Shit/#0004/
    __pattern__ = r'xdcc://([^/]*?)(/#?.*?)?/.*?/#?\d+/?'
    __type__ = "hoster"
    __config__ = [("nick", "str", "Nickname", "pyload"),
                  ("ident", "str", "Ident", "pyloadident"),
                  ("realname", "str", "Realname", "pyloadreal")]
    __description__ = """Download from IRC XDCC bot"""
    __author_name__ = "jeix"
    __author_mail__ = "jeix@hasnomail.com"

    def setup(self):
        self.debug = 0  #: 0,1,2
        self.timeout = 30
        self.multi_dl = False

    def process(self, pyfile):
        # change request type
        self.req = pyfile.manager.pyload.req.get_request(
            self.__name__, type="XDCC")

        self.pyfile = pyfile
        for _ in range(0, 3):
            try:
                nmn = self.do_download(pyfile.url)
                self.log_debug(
                    "{}: Download of {} finished".format(self.__name__, nmn))
                return
            except socket.error as e:
                if hasattr(e, "errno"):
                    errno = e.errno
                else:
                    errno = e.args[0]

                if errno in (10054,):
                    self.log_debug(
                        "XDCC: Server blocked our ip, retry in 5 min")
                    self.set_wait(300)
                    self.wait()
                    continue

                self.fail(
                    _("Failed due to socket errors. Code: {:d}").format(errno))

        self.fail(_("Server blocked our ip, retry again later manually"))

    def do_download(self, url):
        self.pyfile.set_status("waiting")  #: real link

        download_folder = self.pyload.config.get('general', 'storage_folder')
        location = os.path.join(download_folder, self.pyfile.package(
        ).folder.decode(sys.getfilesystemencoding()))
        if not os.path.exists(location):
            makedirs(location)

        m = re.match(r'xdcc://(.*?)/#?(.*?)/(.*?)/#?(\d+)/?', url)
        server = m.group(1)
        chan = m.group(2)
        bot = m.group(3)
        pack = m.group(4)
        nick = self.get_config('nick')
        ident = self.get_config('ident')
        real = self.get_config('realname')

        temp = server.split(':')
        ln = len(temp)
        if ln == 2:
            host, port = temp
        elif ln == 1:
            host, port = temp[0], 6667
        else:
            self.fail(_("Invalid hostname for IRC Server ({})").format(server))

        #######################
        # CONNECT TO IRC AND IDLE FOR REAL LINK
        dl_time = time.time()

        with closing(socket.socket()) as sock:
            sock.connect((host, int(port)))
            if nick == "pyload":
                # last 3 digits
                nick = "pyload-{:d}".format(time.time() % 1000)
            sock.send("NICK {}\r\n".format(nick))
            sock.send("USER {} {} bla :{}\r\n".format(ident, host, real))
            time.sleep(3)
            sock.send("JOIN #{}\r\n".format(chan))
            sock.send("PRIVMSG {} :xdcc send #{}\r\n".format(bot, pack))

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
                        sock.send(
                            "PRIVMSG {} :xdcc send #{}\r\n".format(bot, pack))

                else:
                    if (dl_time + self.timeout) < time.time():  # TODO: add in config
                        sock.send("QUIT :byebye\r\n")
                        # sock.close()
                        self.fail(_("XDCC Bot did not answer"))

                fdset = select([sock], [], [], 0)
                if sock not in fdset[0]:
                    continue

                readbuffer += sock.recv(1024)
                temp = readbuffer.split("\n")
                readbuffer = temp.pop()

                for line in temp:
                    if self.debug is 2:
                        print("*> {}".format(line, errors='ignore'))
                    line = line.rstrip()
                    first = line.split()

                    if first[0] == "PING":
                        sock.send("PONG {}\r\n".format(first[1]))

                    if first[0] == "ERROR":
                        self.fail(_("IRC-Error: {}").format(line))

                    msg = line.split(None, 3)
                    if len(msg) != 4:
                        continue

                    msg = {
                        "origin": msg[0][1:],
                        "action": msg[1],
                        "target": msg[2],
                        "text": msg[3][1:]
                    }

                    if nick == msg['target'][0:len(nick)] and "PRIVMSG" == msg[
                            'action']:
                        if msg['text'] == "\x01VERSION\x01":
                            self.log_debug("XDCC: Sending CTCP VERSION")
                            sock.send("NOTICE {} :{}\r\n".format(
                                msg['origin'], "pyLoad IRC Interface"))
                        elif msg['text'] == "\x01TIME\x01":
                            self.log_debug("Sending CTCP TIME")
                            sock.send("NOTICE {} :{:d}\r\n".format(
                                msg['origin'], time.time()))
                        elif msg['text'] == "\x01LAG\x01":
                            pass  #: do not know how to answer

                    if not (bot == msg['origin'][0:len(bot)]
                            and nick == msg['target'][0:len(nick)]
                            and msg['action'] in ("PRIVMSG", "NOTICE")):
                        continue

                    if self.debug is 1:
                        print("{}: {}".format(msg['origin'], msg['text']))

                    if "You already requested that pack" in msg['text']:
                        retry = time.time() + 300

                    if "you must be on a known channel to request a pack" in msg[
                            'text']:
                        self.fail(_("Wrong channel"))

                    m = re.match(
                        '\x01DCC SEND (.*?) (\d+) (\d+)(?: (\d+))?\x01', msg['text'])
                    if m:
                        done = True

            # get connection data
            ip = socket.inet_ntoa(struct.pack(
                'L', socket.ntohl(int(m.group(2)))))
            port = int(m.group(3))
            packname = m.group(1)

            if len(m.groups()) > 3:
                self.req.filesize = int(m.group(4))

            self.pyfile.name = packname
            filename = format.path(location, packname)
            self.log_info(
                _("XDCC: Downloading {} from {}:{:d}").format(packname, ip, port))

            self.pyfile.set_status("downloading")
            newname = self.req.download(
                ip, port, filename, sock, self.pyfile.set_progress)
            if newname and newname != filename:
                self.log_info(_("{} saved as {}").format(
                    self.pyfile.name, newname))
                filename = newname

            # kill IRC socket
            # sock.send("QUIT :byebye\r\n")

        self.last_download = filename
        return self.last_download
