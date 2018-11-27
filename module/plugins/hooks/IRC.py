# -*- coding: utf-8 -*-

import re
import select
import socket
import time
import traceback
from threading import Thread

import pycurl
import ssl
from module.Api import FileDoesNotExists, PackageDoesNotExists

from ..internal.misc import format_size
from ..internal.Notifier import Notifier


class IRC(Thread, Notifier):
    __name__ = "IRC"
    __type__ = "hook"
    __version__ = "0.26"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("host", "str", "IRC-Server Address", "Enter your server here!"),
                  ("port", "int", "IRC-Server Port", 6667),
                  ("ident", "str", "Clients ident", "pyload-irc"),
                  ("realname", "str", "Realname", "pyload-irc"),
                  ("ssl", "bool", "Use SSL", False),
                  ("nick", "str", "Nickname the Client will take", "pyLoad-IRC"),
                  ("owner", "str", "Nickname the Client will accept commands from", "Enter your nick here!"),
                  ("info_file", "bool", "Inform about every file finished", False),
                  ("info_pack", "bool", "Inform about every package finished", True),
                  ("captcha", "bool", "Send captcha requests", True)]

    __description__ = """Connect to irc and let owner perform different tasks"""
    __license__ = "GPLv3"
    __authors__ = [("Jeix", "Jeix@hasnomail.com")]

    def __init__(self, *args, **kwargs):
        Thread.__init__(self)
        Notifier.__init__(self, *args, **kwargs)
        self.setDaemon(True)

    def activate(self):
        self.abort = False
        self.more = []
        self.new_package = {}

        self.start()

    def package_finished(self, pypack):
        try:
            if self.config.get('info_pack'):
                self.response(_("Package finished: %s") % pypack.name)

        except Exception:
            pass

    def download_finished(self, pyfile):
        try:
            if self.config.get('info_file'):
                self.response(_("Download finished: %s @ %s ") % (pyfile.name, pyfile.pluginname))

        except Exception:
            pass

    def captcha_task(self, task):
        if self.config.get('captcha') and task.isTextual():
            task.handler.append(self)
            task.setWaiting(60)

            html = self.load("http://www.freeimagehosting.net/upl.php",
                             post={'file': (pycurl.FORM_FILE, task.captchaParams['file'])})

            url = re.search(r"src='([^']+)'", html).group(1)
            self.response(_("New Captcha Request: %s") % url)
            self.response(_("Answer with 'c %s text on the captcha'") % task.id)

    def run(self):
        #: Connect to IRC etc.
        self.sock = socket.socket()
        host = self.config.get('host')
        self.sock.connect((host, self.config.get('port')))

        if self.config.get('ssl'):
            self.sock = ssl.wrap_socket(self.sock, cert_reqs=ssl.CERT_NONE)  # @TODO: support certificate

        nick = self.config.get('nick')
        self.sock.send("NICK %s\r\n" % nick)
        self.sock.send("USER %s %s bla :%s\r\n" % (nick, host, nick))
        for t in self.config.get('owner').split():
            if t.strip().startswith("#"):
                self.sock.send("JOIN %s\r\n" % t.strip())
        self.log_info(_("Connected to"), host)
        self.log_info(_("Switching to listening mode!"))
        try:
            self.main_loop()

        except IRCError, ex:
            self.sock.send("QUIT :byebye\r\n")
            if self.pyload.debug:
                traceback.print_exc()
            self.sock.close()

    def main_loop(self):
        readbuffer = ""
        while True:
            time.sleep(1)
            fdset = select.select([self.sock], [], [], 0)
            if self.sock not in fdset[0]:
                continue

            if self.abort:
                raise IRCError("quit")

            readbuffer += self.sock.recv(1024)
            temp = readbuffer.split("\n")
            readbuffer = temp.pop()

            for line in temp:
                line = line.rstrip()
                first = line.split()

                if first[0] == "PING":
                    self.sock.send("PONG :%s\r\n" % first[1])

                if first[0] == "ERROR":
                    raise IRCError(line)

                msg = line.split(None, 3)
                if len(msg) < 4:
                    continue

                msg = {
                    'origin': msg[0][1:],
                    'action': msg[1],
                    'target': msg[2],
                    'text': msg[3][1:]
                }

                self.handle_events(msg)

    def handle_events(self, msg):
        if not msg['origin'].split("!", 1)[0] in self.config.get('owner').split():
            return

        if msg['target'].split("!", 1)[0] != self.config.get('nick'):
            return

        if msg['action'] != "PRIVMSG":
            return

        #: HANDLE CTCP ANTI FLOOD/BOT PROTECTION
        if msg['text'] == "\x01VERSION\x01":
            self.log_debug("Sending CTCP VERSION")
            self.sock.send("NOTICE %s :%s\r\n" % (msg['origin'], "pyLoad! IRC Interface"))
            return

        elif msg['text'] == "\x01TIME\x01":
            self.log_debug("Sending CTCP TIME")
            self.sock.send("NOTICE %s :%d\r\n" % (msg['origin'], time.time()))
            return

        elif msg['text'] == "\x01LAG\x01":
            self.log_debug("Received CTCP LAG")  #: don't know how to answer
            return

        trigger = "pass"
        args = None

        try:
            temp = msg['text'].split()
            trigger = temp[0]
            if len(temp) > 1:
                args = temp[1:]

        except Exception:
            pass

        handler = getattr(self, "event_%s" % trigger, self.event_pass)
        try:
            res = handler(args)
            for line in res:
                self.response(line, msg['origin'])

        except Exception, e:
            self.log_error(e, trace=True)

    def response(self, msg, origin=""):
        if origin == "":
            for t in self.config.get('owner').split():
                self.sock.send("PRIVMSG %s :%s\r\n" % (t.strip(), msg))
        else:
            self.sock.send("PRIVMSG %s :%s\r\n" % (origin.split("!", 1)[0], msg))

    # Events
    def event_pass(self, args):
        return []

    def event_status(self, args):
        downloads = self.pyload.api.statusDownloads()
        if not downloads:
            return ["INFO: There are no active downloads currently."]

        temp_progress = ""
        lines = ["ID - Name - Status - Speed - ETA - Progress"]
        for data in downloads:

            if data.status == 5:
                temp_progress = data.format_wait
            else:
                temp_progress = "%d%% (%s)" % (data.percent, data.format_size)

            lines.append("#%d - %s - %s - %s - %s - %s" % (data.fid, data.name, data.statusmsg,
                                                           "%s/s" % format_size(data.speed),
                                                           "%s" % data.format_eta, temp_progress))
        return lines

    def event_queue(self, args):
        pdata = self.pyload.api.getQueueData()

        if not pdata:
            return ["INFO: There are no packages in queue."]

        lines = []
        for pack in pdata:
            lines.append('PACKAGE #%s: "%s" with %d links.' % (pack.pid, pack.name, len(pack.links)))

        return lines

    def event_collector(self, args):
        pdata = self.pyload.api.getCollectorData()
        if not pdata:
            return ["INFO: No packages in collector!"]

        lines = []
        for pack in pdata:
            lines.append('PACKAGE #%s: "%s" with %d links.' % (pack.pid, pack.name, len(pack.links)))

        return lines

    def event_info(self, args):
        if not args:
            return ["ERROR: Use info like this: info <id>"]

        info = None
        try:
            info = self.pyload.api.getFileData(int(args[0]))

        except FileDoesNotExists:
            return ["ERROR: Link doesn't exists."]

        return ['LINK #%s: %s (%s) [%s][%s]' % (info.fid, info.name, info.format_size, info.statusmsg, info.plugin)]

    def event_packinfo(self, args):
        if not args:
            return ["ERROR: Use packinfo like this: packinfo <id>"]

        lines = []
        pack = None
        try:
            pack = self.pyload.api.getPackageData(int(args[0]))

        except PackageDoesNotExists:
            return ["ERROR: Package doesn't exists."]

        id = args[0]

        self.more = []

        lines.append('PACKAGE #%s: "%s" with %d links' % (id, pack.name, len(pack.links)))
        for pyfile in pack.links:
            self.more.append('LINK #%s: %s (%s) [%s][%s]' % (pyfile.fid, pyfile.name, pyfile.format_size,
                                                             pyfile.statusmsg, pyfile.plugin))

        if len(self.more) < 6:
            lines.extend(self.more)
            self.more = []
        else:
            lines.extend(self.more[:6])
            self.more = self.more[6:]
            lines.append("%d more links do display." % len(self.more))

        return lines

    def event_more(self, args):
        if not self.more:
            return ["No more information to display."]

        lines = self.more[:6]
        self.more = self.more[6:]
        lines.append("%d more links do display." % len(self.more))

        return lines

    def event_start(self, args):
        self.pyload.api.unpauseServer()
        return ["INFO: Starting downloads."]

    def event_stop(self, args):
        self.pyload.api.pauseServer()
        return ["INFO: No new downloads will be started."]

    def event_add(self, args):
        if len(args) < 2:
            return ['ERROR: Add links like this: "add <packagename|id> links". ',
                    "This will add the link <link> to to the package <package> / the package with id <id>!"]

        pack = args[0].strip()
        links = [x.strip() for x in args[1:]]

        try:
            id = int(pack)
            pack = self.pyload.api.getPackageData(id)
            if not pack:
                return ["ERROR: Package doesn't exists."]

            #@TODO: add links

            return ["INFO: Added %d links to Package %s [#%d]" % (len(links), pack['name'], id)]

        except Exception:
            #: Create new package
            id = self.pyload.api.addPackage(pack, links, 1)
            return ["INFO: Created new Package %s [#%d] with %d links." % (pack, id, len(links))]

    def event_del(self, args):
        if len(args) < 2:
            return ["ERROR: Use del command like this: del -p|-l <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"]

        if args[0] == "-p":
            ret = self.pyload.api.deletePackages(map(int, args[1:]))
            return ["INFO: Deleted %d packages!" % len(args[1:])]

        elif args[0] == "-l":
            ret = self.pyload.api.delLinks(map(int, args[1:]))
            return ["INFO: Deleted %d links!" % len(args[1:])]

        else:
            return ["ERROR: Use del command like this: del <-p|-l> <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"]

    def event_push(self, args):
        if not args:
            return ["ERROR: Push package to queue like this: push <package id>"]

        id = int(args[0])
        try:
            self.pyload.api.getPackageInfo(id)
        except PackageDoesNotExists:
            return ["ERROR: Package #%d does not exist." % id]

        self.pyload.api.pushToQueue(id)
        return ["INFO: Pushed package #%d to queue." % id]

    def event_pull(self, args):
        if not args:
            return ["ERROR: Pull package from queue like this: pull <package id>."]

        id = int(args[0])
        if not self.pyload.api.getPackageData(id):
            return ["ERROR: Package #%d does not exist." % id]

        self.pyload.api.pullFromQueue(id)
        return ["INFO: Pulled package #%d from queue to collector." % id]

    def event_c(self, args):
        """
        Captcha answer
        """
        if not args:
            return ["ERROR: Captcha ID missing."]

        task = self.pyload.captchaManager.getTaskByID(args[0])
        if not task:
            return ["ERROR: Captcha Task with ID %s does not exists." % args[0]]

        task.setResult(" ".join(args[1:]))
        return ["INFO: Result %s saved." % " ".join(args[1:])]

    def event_help(self, args):
        lines = ["The following commands are available:",
                 "add <package|packid> <links> [...] Adds link to package. (creates new package if it does not exist)",
                 "queue                       Shows all packages in the queue",
                 "collector                   Shows all packages in collector",
                 "del -p|-l <id> [...]        Deletes all packages|links with the ids specified",
                 "info <id>                   Shows info of the link with id <id>",
                 "packinfo <id>               Shows info of the package with id <id>",
                 "more                        Shows more info when the result was truncated",
                 "start                       Starts all downloads",
                 "stop                        Stops the download (but not abort active downloads)",
                 "push <id>                   Push package to queue",
                 "pull <id>                   Pull package from queue",
                 "status                      Show general download status",
                 "help                        Shows this help message"]
        return lines


class IRCError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
