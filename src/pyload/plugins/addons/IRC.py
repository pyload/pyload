# -*- coding: utf-8 -*-

import re
import select
import socket
import ssl
import time

import pycurl
from pyload.core.utils.convert import to_bytes, to_str

from ..base.chat_bot import ChatBot


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


class IRC(ChatBot):
    __name__ = "IRC"
    __type__ = "addon"
    __version__ = "0.29"
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
    __authors__ = [
        ("Jeix", "Jeix@hasnomail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")
    ]

    def activate(self):
        self.abort = False

        super().activate()

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
                self._("Answer with 'ca {} text on the captcha'").format(task.id)
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
        self.log_info(self._("Connecting as"), nick)
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
                    self.sock.send(to_bytes("PONG :{}\r\n".format(args[0])))

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
            ctcp_args = ctcp_data[1] if len(ctcp_data) > 1 else ""

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

        temp = text.split()
        try:
            command = temp[0]
            args = text.split()[1:]

        except IndexError:
            command = "error"
            args = []

        try:
            res = self.do_bot_command(command, args)

            for line in res:
                self.response(line, msg["origin"])
                time.sleep(1)  #: avoid Excess Flood

        except Exception as exc:
            self.log_error(exc)

    def response(self, msg, origin=""):
        if origin == "":
            for t in self.config.get("owner").split():
                self.sock.send(to_bytes("PRIVMSG {} :{}\r\n".format(t.strip(), msg)))
        else:
            self.sock.send(to_bytes("PRIVMSG {} :{}\r\n".format(origin.split("!", 1)[0], msg)))

    def exit(self):
        self.sock.send(b"QUIT :byebye\r\n")
        self.sock.close()


class IRCError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
