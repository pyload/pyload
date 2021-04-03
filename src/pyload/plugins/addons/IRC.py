# -*- coding: utf-8 -*-

import re
import select
import socket
import ssl
import time
from threading import Thread

import pycurl
from pyload.core.api import FileDoesNotExists, PackageDoesNotExists
from pyload.core.utils import format
from pyload.core.utils.convert import to_bytes, to_str

from ..base.notifier import Notifier


def parse_irc_msg(line):
    """
    Breaks a message from an IRC server into its origin, command, and arguments.
    """
    origin = ''
    if not line:
        return None, None, None

    if line[0:1] == b':':
        origin, line = line[1:].split(b' ', 1)

    if line.find(b' :') != -1:
        line, trailing = line.split(b' :', 1)
        args = line.split()
        args.append(trailing)

    else:
        args = line.split()

    command = args.pop(0)

    return to_str(origin), to_str(command), [to_str(arg) for arg in args]


class IRC(Thread, Notifier):
    __name__ = "IRC"
    __type__ = "addon"
    __version__ = "0.28"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("host", "str", "IRC-Server Address", "Enter your server here!"),
        ("port", "int", "IRC-Server Port", 6667),
        ("ident", "str", "Clients ident", "pyload-irc"),
        ("realname", "str", "Realname", "pyload-irc"),
        ("ssl", "bool", "Use SSL", False),
        ("nick", "str", "Nickname the Client will take", "pyLoad-IRC"),
        (
            "owner",
            "str",
            "Nickname the Client will accept commands from",
            "Enter your nick here!",
        ),
        ("info_file", "bool", "Inform about every file finished", False),
        ("info_pack", "bool", "Inform about every package finished", True),
        ("captcha", "bool", "Send captcha requests", True),
        ("maxline", "int", "Maximum line per message", 6)
    ]

    __description__ = """Connect to irc and let owner perform different tasks"""
    __license__ = "GPLv3"
    __authors__ = [("Jeix", "Jeix@hasnomail.com")]

    def __init__(self, *args, **kwargs):
        Thread.__init__(self)
        Notifier.__init__(self, *args, **kwargs)
        self.daemon = True

    def activate(self):
        self.abort = False
        self.more = []
        self.new_package = {}

        self.start()

    def package_finished(self, pypack):
        try:
            if self.config.get("info_pack"):
                self.response(self._("Package finished: {}").format(pypack.name))

        except Exception:
            pass

    def download_finished(self, pyfile):
        try:
            if self.config.get("info_file"):
                self.response(
                    self._("Download finished: {name} @ {plugin} ").format(
                        name=pyfile.name, plugin=pyfile.pluginname
                    )
                )

        except Exception:
            pass

    def captcha_task(self, task):
        if self.config.get("captcha") and task.is_textual():
            task.handler.append(self)
            task.set_waiting(60)

            html = self.load(
                "http://www.freeimagehosting.net/upl.php",
                post={"file": (pycurl.FORM_FILE, task.captcha_params["file"])},
            )

            url = re.search(r"src='([^']+)'", html).group(1)
            self.response(self._("New Captcha Request: {}").format(url))
            self.response(
                self._("Answer with 'c {} text on the captcha'").format(task.id)
            )

    def run(self):
        #: Connect to IRC etc.
        self.sock = socket.socket()
        host = self.config.get("host")
        self.sock.connect((host, self.config.get("port")))

        if self.config.get("ssl"):
            self.sock = ssl.wrap_socket(
                self.sock, cert_reqs=ssl.CERT_NONE
            )  # TODO: support certificate

        nick = self.config.get("nick")
        self.sock.send(to_bytes("NICK {}\r\n".format(nick)))
        self.sock.send(to_bytes("USER {} {} bla :{}\r\n".format(nick, host, nick)))
        self.log_info(self._("Connected to"), host)
        for t in self.config.get("owner").split():
            if t.startswith("#"):
                self.sock.send(to_bytes("JOIN {}\r\n".format(t)))
                self.log_info(self._("Joined channel {}").format(to_str(t)))
        self.log_info(self._("Switching to listening mode!"))
        try:
            self.main_loop()

        except IRCError:
            self.sock.send(b"QUIT :byebye\r\n")
            self.sock.close()

    def main_loop(self):
        readbuffer = b""
        while True:
            time.sleep(1)
            fdset = select.select([self.sock], [], [], 0)
            if self.sock not in fdset[0]:
                continue

            if self.abort:
                raise IRCError("quit")

            readbuffer += self.sock.recv(1 << 10)
            temp = readbuffer.split(b"\n")
            readbuffer = temp.pop()

            for line in temp:
                line = line.rstrip()
                origin, command, args = parse_irc_msg(line)

                if command == "PING":
                    self.log_debug("[{}] Ping? Pong!".format(args[0]))
                    self.sock.send(to_bytes("PONG :%s\r\n" % args[0]))

                if command == "ERROR":
                    raise IRCError(line)

                msg = {
                    "origin": origin,
                    "command": command,
                    "args": args,
                }

                self.handle_events(msg)

    def handle_events(self, msg):
        if msg["command"] != "PRIVMSG" or not msg["origin"]:
            return

        sender_nick = msg["origin"].split('@')[0].split('!')[0]
        recipient = msg["args"][0]
        text = msg["args"][1]

        if recipient != self.config.get("nick"):
            return

        #: HANDLE CTCP ANTI FLOOD/BOT PROTECTION
        if text[0] == '\x01' and text[-1] == '\x01':  #: CTCP
            ctcp_data = text[1:-1].split(' ', 1)
            ctcp_command = ctcp_data[0]
            ctcp_args    = ctcp_data[1] if len(ctcp_data) > 1 else ""

            if ctcp_command == "VERSION":
                self.log_debug("Sending CTCP VERSION")
                self.sock.send(
                    to_bytes("NOTICE {} :{}\r\n".format(msg["origin"], "pyLoad! IRC Interface"))
                )
                return
            elif ctcp_command == "TIME":
                self.log_debug("Sending CTCP TIME")
                self.sock.send(to_bytes("NOTICE {} :{}\r\n".format(msg["origin"], time.time())))
                return
            elif ctcp_command == "PING":
                self.log_debug("[{}] Ping? Pong!".format(sender_nick))
                self.sock.send(to_bytes("NOTICE {} :\x01PING {}\x01\r\n".format(sender_nick, ctcp_args)))  #@NOTE: PING is not a typo
            elif ctcp_command == "LAG":
                self.log_debug("Received CTCP LAG")  #: don't know how to answer
                return

        if sender_nick not in self.config.get("owner").split():
            return

        args = []
        try:
            trigger = text.split()[0]
            args = text.split()[1:]

        except IndexError:
            trigger = "pass"

        handler = getattr(self, "event_{}".format(trigger), self.event_pass)
        try:
            res = handler(args)
            for line in res:
                self.response(line, msg["origin"])
                time.sleep(0.5)

        except Exception as exc:
            self.log_error(exc)

    def response(self, msg, origin=""):
        if origin == "":
            for t in self.config.get("owner").split():
                self.sock.send(to_bytes("PRIVMSG {} :{}\r\n".format(t.strip(), msg)))
        else:
            self.sock.send(to_bytes("PRIVMSG {} :{}\r\n".format(origin.split("!", 1)[0], msg)))

    # Events
    def event_pass(self, args):
        return []

    def event_status(self, args):
        downloads = self.pyload.api.status_downloads()
        if not downloads:
            return ["INFO: There are no active downloads currently."]

        temp_progress = ""
        lines = ["ID - Name - Status - Speed - ETA - Progress"]
        for data in downloads:
            if data.status == 5:
                temp_progress = data.format_wait
            else:
                temp_progress = "{}% ({})".format(data.percent, data.format_size)

            lines.append(
                "#{} - {} - {} - {} - {} - {}".format(
                    data.fid,
                    data.name,
                    data.statusmsg,
                    "{}".format(format.speed(data.speed)),
                    "{}".format(data.format_eta),
                    temp_progress,
                )
            )
        return lines

    def event_queue(self, args):
        pdata = self.pyload.api.get_queue_data()

        if not pdata:
            return ["INFO: There are no packages in queue."]

        lines = []
        for pack in pdata:
            lines.append(
                'PACKAGE #{}: "{}" with {} links.'.format(
                    pack.pid, pack.name, len(pack.links)
                )
            )

        return lines

    def event_collector(self, args):
        pdata = self.pyload.api.get_collector_data()
        if not pdata:
            return ["INFO: No packages in collector!"]

        lines = []
        for pack in pdata:
            lines.append(
                'PACKAGE #{}: "{}" with {} links.'.format(
                    pack.pid, pack.name, len(pack.links)
                )
            )

        return lines

    def event_info(self, args):
        if not args:
            return ["ERROR: Use info like this: info <id>"]

        try:
            info = self.pyload.api.get_file_data(int(args[0]))

        except FileDoesNotExists:
            return ["ERROR: Link doesn't exists."]

        return [
            "LINK #{}: {} ({}) [{}][{}]".format(
                info.fid, info.name, info.format_size, info.statusmsg, info.plugin
            )
        ]

    def event_packinfo(self, args):
        if not args:
            return ["ERROR: Use packinfo like this: packinfo <name|id>"]

        lines = []
        id_or_name = args[0]
        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            return ["ERROR: Package doesn't exists."]

        self.more = []

        lines.append(
            'PACKAGE #{}: "{}" with {} links'.format(pack.pid, pack.name, len(pack.links))
        )
        for pyfile in pack.links:
            self.more.append(
                "LINK #{}: {} ({}) [{}][{}]".format(
                    pyfile.fid,
                    pyfile.name,
                    pyfile.format_size,
                    pyfile.statusmsg,
                    pyfile.plugin,
                )
            )

        maxline = self.config.get('maxline')
        if len(self.more) < maxline:
            lines.extend(self.more)
            self.more = []
        else:
            lines.extend(self.more[:maxline])
            self.more = self.more[maxline:]
            lines.append("{} more links do display.".format(len(self.more)))

        return lines

    def event_more(self, args):
        if not self.more:
            return ["No more information to display."]

        maxline = self.config.get('maxline')
        lines = self.more[:maxline]
        self.more = self.more[maxline:]
        lines.append("{} more links do display.".format(len(self.more)))

        return lines

    def event_unpause(self, args):
        self.pyload.api.unpause_server()
        return ["INFO: Starting downloads."]

    def event_pause(self, args):
        self.pyload.api.pause_server()
        return ["INFO: No new downloads will be started."]

    def event_togglepause(self, args):
        if self.pyload.api.toggle_pause():
            return ["INFO: Starting downloads."]
        else:
            return ["INFO: No new downloads will be started."]

    def event_add(self, args):
        if len(args) < 2:
            return [
                'ERROR: Add links like this: "add <packagename|id> links". ',
                "This will add the link <link> to to the package <package> / the package with id <id>!",
            ]

        id_or_name = args[0].strip()
        links = [x.strip() for x in args[1:]]

        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            #: Create new package
            id = self.pyload.api.add_package(id_or_name, links, 1)
            return [
                "INFO: Created new Package {} [#{}] with {} links.".format(
                    id_or_name, id, len(links)
                )
            ]

        self.pyload.api.add_files(pack.pid, links)
        return [
            "INFO: Added {} links to Package {} [#{}]".format(
                len(links), pack.name, pack.pid
            )
        ]

    def event_del(self, args):
        if len(args) < 2:
            return [
                "ERROR: Use del command like this: del -p|-l <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"
            ]

        if args[0] == "-p":
            ret = self.pyload.api.delete_packages(int(arg) for arg in args[1:])
            return ["INFO: Deleted {} packages!".format(len(args[1:]))]

        elif args[0] == "-l":
            ret = self.pyload.api.del_links(int(arg) for arg in args[1:])
            return ["INFO: Deleted {} links!".format(len(args[1:]))]

        else:
            return [
                "ERROR: Use del command like this: del <-p|-l> <id> [...] (-p indicates that the ids are from packages, -l indicates that the ids are from links)"
            ]

    def event_push(self, args):
        if not args:
            return ["ERROR: Push package to queue like this: push <package id>"]

        package_id = int(args[0])
        try:
            self.pyload.api.get_package_info(package_id)
        except PackageDoesNotExists:
            return ["ERROR: Package #{} does not exist.".format(package_id)]

        self.pyload.api.push_to_queue(package_id)
        return ["INFO: Pushed package #{} to queue.".format(package_id)]

    def event_pull(self, args):
        if not args:
            return ["ERROR: Pull package from queue like this: pull <package id>."]

        package_id = int(args[0])
        if not self.pyload.api.get_package_data(package_id):
            return ["ERROR: Package #{} does not exist.".format(package_id)]

        self.pyload.api.pull_from_queue(package_id)
        return ["INFO: Pulled package #{} from queue to collector.".format(package_id)]

    def event_c(self, args):
        """
        Captcha answer.
        """
        if not args:
            return ["ERROR: Captcha ID missing."]

        task = self.pyload.captcha_manager.get_task_by_id(args[0])
        if not task:
            return ["ERROR: Captcha Task with ID {} does not exists.".format(args[0])]

        task.set_result(" ".join(args[1:]))
        return ["INFO: Result {} saved.".format(" ".join(args[1:]))]

    def event_freespace(self, args):
        b = format.size(int(self.pyload.api.free_space()))
        return ["INFO: Free space is {}.".format(b)]

    def event_restart(self, args):
        self.pyload.api.restart()
        return ["INFO: Done."]

    def event_restartfailed(self, args):
        self.pyload.api.restart_failed()
        return ["INFO: Restarting all failed downloads."]

    def event_restartfile(self, args):
        if not args:
            return ['ERROR: missing argument']
        id = int(args[0])
        if not self.pyload.api.get_file_data(id):
            return ["ERROR: File #{} does not exist.".format(id)]
        self.pyload.api.restart_file(id)
        return ["INFO: Restart file #{}.".format(id)]

    def event_restartpackage(self, args):
        if not args:
            return ['ERROR: missing argument']
        id_or_name = args[0]
        pack = self._get_package_by_name_or_id(id_or_name)
        if not pack:
            return ["ERROR: Package #{} does not exist.".format(id_or_name)]
        self.pyload.api.restart_package(pack.pid)
        return ["INFO: Restart package {} (#{}).".format(pack.name, pack.pid)]

    def event_deletefinished(self, args):
        return ["INFO: Deleted package ids: {}.".format(self.pyload.api.delete_finished())]

    def event_getlog(self, args):
        """Returns most recent log entries."""
        self.more = []
        lines = []
        log = self.pyload.api.get_log()

        for line in log:
            if line:
                if line[-1] == '\n':
                    line = line[:-1]
                self.more.append("LOG: {}".format(line))

        maxline = self.config.get('maxline')
        if args and args[0] == 'last':
            if len(args) < 2:
                self.more = self.more[-maxline:]
            else:
                self.more = self.more[-(int(args[1])):]

        if len(self.more) < maxline:
            lines.extend(self.more)
            self.more = []
        else:
            lines.extend(self.more[:maxline])
            self.more = self.more[maxline:]
            lines.append("{} more logs do display.".format(len(self.more)))

        return lines

    def event_help(self, args):
        lines = [
            "The following commands are available:",
            "add <package|packid> <links> [...] Adds link to package. (creates new package if it does not exist)",
            "collector                          Shows all packages in collector",
            "del -p|-l <id> [...]               Deletes all packages|links with the ids specified",
            "deletefinished                     Deletes all finished files and completly finished packages",
            "freespace                          Available free space at download directory in bytes",
            "getlog [last [nb]]                 Returns most recent log entries",
            "help                               Shows this help message",
            "info <id>                          Shows info of the link with id <id>",
            "more                               Shows more info when the result was truncated",
            "packinfo <package|packid>          Shows info of the package with id <id>",
            "pause                              Stops the download (but not abort active downloads)",
            "pull <id>                          Pull package from queue",
            "push <id>                          Push package to queue",
            "queue                              Shows all packages in the queue",
            "restart                            Restart pyload core",
            "restartfailed                      Restarts all failed files",
            "restartfile <id>                   Resets file status, so it will be downloaded again",
            "restartpackage <package|packid>    Restarts a package, resets every containing files",
            "status                             Show general download status",
            "togglepause                        Toggle pause state",
            "unpause                            Starts all downloads"
        ]
        return lines

    # End events

    def _get_package_by_name_or_id(self, id_or_name):
        """Return the first packageData found or None."""
        pack = None
        if id_or_name.isdigit():
            try:
                package_id = int(id_or_name)
                pack = self.pyload.api.get_package_data(package_id)
            except PackageDoesNotExists:
                pack = self._get_package_by_name(id_or_name)
        else:
            pack = self._get_package_by_name(id_or_name)
        return pack

    def _get_package_by_name(self, name):
        """Return the first packageData found or None."""

        pq = self.pyload.api.get_queue_data()
        for pack in pq:
            if pack.name == name:
                self.log_debug('pack.name', pack.name, 'pack.pid', pack.pid)
                return pack

        pc = self.pyload.api.get_collector()
        for pack in pc:
            if pack.name == name:
                self.log_debug('pack.name', pack.name, 'pack.pid', pack.pid)
                return pack
        return None


class IRCError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
