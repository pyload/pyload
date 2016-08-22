# -*- coding: utf-8 -*-

import os
import re
import select
import socket
import struct
import time

from module.plugins.internal.Hoster import Hoster
from module.plugins.internal.misc import exists, fsjoin
from module.plugins.Plugin import Abort

# try:
#     no_socks = False
#     import socks
#
# except ImportError:
#     no_socks = True





class IRC(object):
    def __init__(self, plugin, nick, ident ,realname, ctcp_version):
        self.plugin = plugin

        self.nick         = "pyload-%d" % (time.time() % 1000) if nick == "pyload" else nick  #: last 3 digits
        self.ident        = ident
        self.realname     = realname
        self.ctcp_version = ctcp_version

        self.irc_sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_buffer = ""
        self.lines          = []

        self.connected      = False
        self.host           = ""
        self.port           = 0

        self.xdcc_request_time = None


    def _data_available(self):
        fdset = select.select([self.irc_sock], [], [], 0)
        return True if self.irc_sock in fdset[0] else False


    def _get_response_line(self, timeout=5):
        start_time = time.time()
        while time.time()-start_time < timeout:
            if self._data_available():
                self.receive_buffer += self.irc_sock.recv(1024)
                self.lines += self.receive_buffer.split("\r\n")
                self.receive_buffer = self.lines.pop()

            if self.lines:
                return self.lines.pop(0)

            else:
                time.sleep(0.1)

        return None


    def _parse_irc_msg(self, line):
        """
        Breaks a message from an IRC server into its origin, command, and arguments.
        """
        origin = ''
        if not line:
            return None, None, None

        if line[0] == ':':
            origin, line = line[1:].split(' ', 1)

        if line.find(' :') != -1:
            line, trailing = line.split(' :', 1)
            args = line.split()
            args.append(trailing)

        else:
            args = line.split()

        command = args.pop(0)

        return origin, command, args


    def _keep_alive(self):
        if not self._data_available():
            return

        self.receive_buffer += self.irc_sock.recv(1024)
        lines = self.receive_buffer.split("\n")
        self.receive_buffer = lines.pop()

        for line in lines:
            line = line.rstrip()
            first = line.split()
            if first[0] == "PING":
                self.irc_sock.send("PONG %s\r\n" % first[1])


    def connect_server(self, host, port):
        """
        Connect to the IRC server and wait for RPL_WELCOME message
        """
        self.plugin.log_info(_("Connecting to: %s:%s") % (host, port))

        self.irc_sock.settimeout(30)
        self.irc_sock.connect((host, port))
        self.irc_sock.settimeout(None)

        self.irc_sock.send("NICK %s\r\n" % self.nick)
        self.irc_sock.send("USER %s %s bla :%s\r\n" % (self.ident, host, self.realname))

        start_time = time.time()
        while time.time()-start_time < 30:
            origin, command, args = self.get_irc_command()
            if command == "001":  #: RPL_WELCOME
                self.connected = True
                self.host      = host
                self.port      = port

                start_time = time.time()
                while self._get_response_line() and time.time()-start_time < 30:  #: Skip MOTD
                    pass

                self.plugin.log_info(_("Successfully connected to %s:%s") % (host, port))

                return True

        self.plugin.log_error(_("Connection to %s:%s failed.") % (host, port))
        return False


    def disconnect_server(self):
        if self.connected:
            self.plugin.log_info(_("Diconnecting from %s:%s") % (self.host, self.port))
            self.irc_sock.send("QUIT :byebye\r\n")
            self.plugin.log_debug("QUIT: %s" % self._get_response_line())
            self.plugin.log_info(_("Disconnected"))
        else:
            self.plugin.log_warning(_("Not connected to server, cannot disconnect"))

        self.irc_sock.close()


    def get_irc_command(self):
        while True:
            line = self._get_response_line()
            origin, command, args = self._parse_irc_msg(line)

            if command == "PING":
                self.plugin.log_debug(_("[%s] PING") % args[0])
                self.irc_sock.send("PONG %s\r\n" % args[0])

            elif command == "PRIVMSG":
                target = args[0]
                text = args[1]
                if target[0:len(self.nick)] == self.nick:
                    if text == "\x01VERSION\x01":
                        self.plugin.log_debug(_("Sending CTCP VERSION"))
                        self.irc_sock.send("NOTICE %s :%s\r\n" % (origin, self.ctcp_version))

                    elif text == "\x01TIME\x01":
                        self.plugin.log_debug(_("Sending CTCP TIME"))
                        self.irc_sock.send("NOTICE %s :%d\r\n" % (origin, time.time()))

                    elif text == "\x01LAG\x01":
                        pass  #: don't know how to answer

                    else:
                        return origin, command, args

                else:
                    return origin, command, args

            else:
                return origin, command, args


    def join_channel(self, chan):
        self.irc_sock.send("JOIN #%s\r\n" % chan)

    def request_xdcc_pack(self, bot, pack):
        self.plugin.log_info(_("Requesting pack #%s") % pack)
        self.xdcc_request_time = time.time()
        self.irc_sock.send("PRIVMSG %s :xdcc send #%s\r\n" % (bot, pack))


class XDCCRequest(object):
    def __init__(self, timeout=30, proxies={}):
        self.proxies = proxies
        self.timeout = timeout

        self.file_size = 0
        self.bytes_received = 0
        self.speed = 0
        self.abort = False


    def create_socket(self):
        # proxy_type = None
        # proxy = None
        #
        # if self.proxies.has_key("socks5"):
        #     proxy_type = socks.PROXY_TYPE_SOCKS5
        #     proxy = self.proxies["socks5"]
        #
        # elif self.proxies.has_key("socks4"):
        #     proxy_type = socks.PROXY_TYPE_SOCKS4
        #     proxy = self.proxies["socks4"]
        #
        # if proxy_type:
        #     sock = socks.socksocket()
        #     t = _parse_proxy(proxy)
        #     sock.setproxy(proxy_type, addr=t[3].split(":")[0], port=int(t[3].split(":")[1]), username=t[1], password=t[2])
        #
        # else:
        #     sock = socket.socket()
        #
        # return sock

        return socket.socket()


    def download(self, ip, port, filename, progress_notify=None):
        last_update = time.time()
        received_bytes = 0

        dcc_sock = self.create_socket()

        dcc_sock.settimeout(self.timeout)
        dcc_sock.connect((ip, port))

        if exists(filename):
            i = 0
            nameParts = filename.rpartition(".")
            while True:
                new_filename = "%s-%d%s%s" % (nameParts[0], i, nameParts[1], nameParts[2])
                i += 1

                if not exists(new_filename):
                    filename = new_filename
                    break

        fh = open(filename, "wb")

        # recv loop for dcc socket
        while True:
            if self.abort:
                dcc_sock.close()
                fh.close()
                os.remove(filename)
                raise Abort()

            self._keep_alive()

            data = dcc_sock.recv(4096)
            dataLen = len(data)
            self.bytes_received += dataLen

            received_bytes += dataLen

            now = time.time()
            timespan = now - last_update
            if timespan > 1:
                self.speed = received_bytes / timespan
                received_bytes = 0
                last_update = now

                if progress_notify:
                    progress_notify(self.percent)

            if not data:
                break

            fh.write(data)

            # acknowledge data by sending number of recceived bytes
            dcc_sock.send(struct.pack('!I', self.bytes_received))

        dcc_sock.close()
        fh.close()

        return filename


    def _data_availible(self, sock):
        fdset = select.select([sock], [], [], 0)
        return sock in fdset[0]


    def _keep_alive(self):
        if not self._data_availible(self.irc_sock):
            return

        self.irc_buffer += self.irc_sock.recv(1024)
        lines = self.irc_buffer.split("\n")
        self.irc_buffer = lines.pop()

        for line in lines:
            line  = line.rstrip()
            first = line.split()
            if first[0] == "PING":
                self.irc_sock.send("PONG %s\r\n" % first[1])


    def abortDownloads(self):
        self.abort = True

    @property
    def size(self):
        return self.file_size

    @property
    def arrived(self):
        return self.bytes_received

    @property
    def percent(self):
        if not self.file_size: return 0
        return (self.bytes_received * 100) / self.file_size

    def close(self):
        pass

# =======================================================================
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
        server, chan, bot, pack = re.match(self.__pattern__, pyfile.url).groups()
        temp = server.split(':')
        ln = len(temp)
        if ln == 2:
            host, port = temp[0], int(temp[1])

        elif ln == 1:
            host, port = temp[0], 6667

        else:
            self.fail(_("Invalid hostname for IRC Server: %s") % server)

        nick          = self.config.get('nick')
        ident         = self.config.get('ident')
        realname      = self.config.get('realname')
        ctcp_version  = self.config.get('ctcp_version')

        #: Change request type
        self.req = self.pyload.requestFactory.getRequest(self.classname, type="XDCC")
        # self.req = XDCCRequest(proxies=self.pyload.requestFactory.getProxies())

        irc_client = IRC(self, nick, ident, realname, ctcp_version)
        for _i in xrange(0, 3):
            try:
                if irc_client.connect_server(host, port):
                    try:
                        irc_client.join_channel(chan)
                        while not self.pyfile.abort:
                            origin, command, args = irc_client.get_irc_command()
                            if origin[0:len(bot)] != bot \
                                    or args[0][0:len(nick)] != nick \
                                    or command not in ("PRIVMSG", "NOTICE"):
                                continue

                            text = args[1]
                            self.log_info(_("PrivMsg: <%s> %s") % (bot, text))

                            if "You already requested that pack" in text:
                                retry = time.time() + 300

                            elif "you must be on a known channel to request a pack" in text:
                                self.log_error(_("Invalid channel"))
                                self.fail(_("Invalid channel"))

                    finally:
                        irc_client.disconnect_server()
                return
                irc_client.request_xdcc_pack(bot, pack)

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

        newname = self.req.download(ip, port, dl_file, self.pyfile.setProgress)
        if newname and newname != dl_file:
            self.log_info(_("%(name)s saved as %(newname)s") % {'name': self.pyfile.name, 'newname': newname})
            dl_file = newname

        #: kill IRC socket
        #: sock.send("QUIT :byebye\r\n")
        sock.close()

        self.last_download = dl_file
        return self.last_download
