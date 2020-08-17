# -*- coding: utf-8 -*-

import os
import re
import select
import socket
import struct
import sys
import threading
import time

from pyload.core.network.exceptions import Abort
from pyload.core.utils.old import lock

from ..base.addon import threaded
from ..base.downloader import BaseDownloader


class IRC:
    def __init__(self, plugin, nick, ident, realname):
        self.plugin = plugin
        self._ = plugin._
        self.lock = threading.RLock()

        #: last 4 digits
        self.nick = (
            "pyload-{:04}".format(time.time() % 10000) if nick == "pyload" else nick
        )
        self.ident = ident
        self.realname = realname

        self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_buffer = ""
        self.lines = []

        self.connected = False
        self.host = ""
        self.port = 0

        self.bot_host = {}

        self.xdcc_request_time = None

    def _data_available(self):
        fdset = select.select([self.irc_sock], [], [], 0)
        return self.irc_sock in fdset[0]

    def _get_response_line(self, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._data_available():
                self.receive_buffer += self.irc_sock.recv(1 << 10)
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
        origin = ""
        if not line:
            return None, None, None

        if line[0] == ":":
            origin, line = line[1:].split(" ", 1)

        if line.find(" :") != -1:
            line, trailing = line.split(" :", 1)
            args = line.split()
            args.append(trailing)

        else:
            args = line.split()

        command = args.pop(0)

        return origin, command, args

    @lock
    def connect_server(self, host, port):
        """
        Connect to the IRC server and wait for RPL_WELCOME message.
        """
        if self.connected:
            self.plugin.log_warning(
                self._("Already connected to server, not connecting")
            )
            return False

        self.plugin.log_info(self._("Connecting to: {}:{}").format(host, port))

        self.irc_sock.setTimeout(30)
        self.irc_sock.connect((host, port))
        self.irc_sock.setTimeout(None)

        self.irc_sock.send("NICK {}\r\n".format(self.nick))
        self.irc_sock.send(
            "USER {} {} bla :{}\r\n".format(self.ident, host, self.realname)
        )

        start_time = time.time()
        while time.time() - start_time < 30:
            origin, command, args = self.get_irc_command()
            if command == "001":  #: RPL_WELCOME
                self.connected = True
                self.host = host
                self.port = port

                start_time = time.time()
                while (
                    self._get_response_line() and time.time() - start_time < 30
                ):  #: Skip MOTD
                    pass

                self.plugin.log_debug(
                    self._("Successfully connected to {}:{}").format(host, port)
                )

                return True

        self.plugin.log_error(self._("Connection to {}:{} failed").format(host, port))

        return False

    @lock
    def disconnect_server(self):
        if self.connected:
            self.plugin.log_info(
                self._("Diconnecting from {}:{}").format(self.host, self.port)
            )
            self.irc_sock.send("QUIT :byebye\r\n")
            self.plugin.log_debug("Disconnected")
            self.connected = False

        else:
            self.plugin.log_warning(
                self._("Not connected to server, cannot disconnect")
            )

        self.irc_sock.close()

    @lock
    def get_irc_command(self):
        origin, command, args = None, None, None
        while True:
            line = self._get_response_line()
            origin, command, args = self._parse_irc_msg(line)

            if command == "PING":
                self.plugin.log_debug(f"[{args[0]}] Ping? Pong!")
                self.irc_sock.send("PONG :{}\r\n".format(args[0]))

            elif origin and command == "PRIVMSG":
                sender_nick = origin.split("@")[0].split("!")[0]
                recipient = args[0]
                text = args[1]

                if text[0] == "\x01" and text[-1] == "\x01":  #: CTCP
                    ctcp_data = text[1:-1].split(" ", 1)
                    ctcp_command = ctcp_data[0]
                    ctcp_args = ctcp_data[1] if len(ctcp_data) > 1 else ""

                    if recipient[0 : len(self.nick)] == self.nick:
                        if ctcp_command == "VERSION":
                            self.plugin.log_debug(
                                self._("[{}] CTCP VERSION").format(sender_nick)
                            )
                            self.irc_sock.send(
                                "NOTICE {} :\x01VERSION {}\x01\r\n".format(
                                    sender_nick, "pyLoad! IRC Interface"
                                )
                            )

                        elif ctcp_command == "TIME":
                            self.plugin.log_debug(
                                self._("[{}] CTCP TIME").format(sender_nick)
                            )
                            self.irc_sock.send(
                                "NOTICE {} :\x01{}\x01\r\n".format(
                                    sender_nick, time.strftime("%a %b %d %H:%M:%S %Y")
                                )
                            )

                        elif ctcp_command == "PING":
                            self.plugin.log_debug(
                                self._("[{}] Ping? Pong!").format(sender_nick)
                            )
                            self.irc_sock.send(
                                "NOTICE {} :\x01PING {}\x01\r\n".format(
                                    sender_nick, ctcp_args
                                )
                            )  # NOTE: PING is not a typo

                        else:
                            break

                else:
                    break

            else:
                break

        return origin, command, args

    @lock
    def join_channel(self, chan):
        chan = "#" + chan if chan[0] != "#" else chan

        self.plugin.log_info(self._("Joining channel {}").format(chan))
        self.irc_sock.send("JOIN {}\r\n".format(chan))

        start_time = time.time()
        while time.time() - start_time < 30:
            origin, command, args = self.get_irc_command()

            #: ERR_KEYSET, ERR_CHANNELISFULL, ERR_INVITEONLYCHAN, ERR_BANNEDFROMCHAN, ERR_BADCHANNELKEY
            if (
                command in ("467", "471", "473", "474", "475")
                and args[1].lower() == chan.lower()
            ):
                self.plugin.log_error(
                    self._("Cannot join channel {} (error {}: '{}')").format(
                        chan, command, args[2]
                    )
                )
                return False

            elif command == "353" and args[2].lower() == chan.lower():  #: RPL_NAMREPLY
                self.plugin.log_debug(f"Successfully joined channel {chan}")
                return True

        return False

    @lock
    def nickserv_identify(self, password):
        self.plugin.log_info(self._("Authenticating nickname"))

        bot = "nickserv"
        bot_host = self.get_bot_host(bot)

        if not bot_host:
            self.plugin.log_warning(
                self._("Server does not seems to support nickserv commands")
            )
            return

        self.irc_sock.send("PRIVMSG {} :identify {}\r\n".format(bot, password))

        start_time = time.time()
        while time.time() - start_time < 30:
            origin, command, args = self.get_irc_command()

            if origin is None or command is None or args is None:
                return

            # Private message from bot to us?
            if (
                "@" not in origin
                or (origin[0 : len(bot)] != bot and origin.split("@")[1] != bot_host)
                or args[0][0 : len(self.nick)] != self.nick
                or command not in ("PRIVMSG", "NOTICE")
            ):
                continue

            try:
                text = str(args[1], "utf-8")
            except UnicodeDecodeError:
                text = str(args[1], "latin1", "replace")

            sender_nick = origin.split("@")[0].split("!")[0]
            self.plugin.log_info(self._("PrivMsg: <{}> {}").format(sender_nick, text))
            break

        else:
            self.plugin.log_warning(
                self._("'{}' did not respond to the request").format(bot)
            )

    @lock
    def send_invite_request(self, bot, chan, password):
        bot_host = self.get_bot_host(bot)
        if bot_host:
            self.plugin.log_info(
                self._("Sending invite request for #{} to '{}'").format(chan, bot)
            )
        else:
            self.plugin.log_warning(self._("Cannot send invite request"))
            return

        self.irc_sock.send(
            "PRIVMSG {} :enter #{} {} {}\r\n".format(bot, chan, self.nick, password)
        )
        start_time = time.time()
        while time.time() - start_time < 30:
            origin, command, args = self.get_irc_command()

            if origin is None or command is None or args is None:
                return

            # Private message from bot to us?
            if (
                "@" not in origin
                or (origin[0 : len(bot)] != bot and origin.split("@")[1] != bot_host)
                or args[0][0 : len(self.nick)] != self.nick
                or command not in ("PRIVMSG", "NOTICE", "INVITE")
            ):
                continue

            try:
                text = str(args[1], "utf-8")
            except UnicodeDecodeError:
                text = str(args[1], "latin1", "replace")

            sender_nick = origin.split("@")[0].split("!")[0]
            if command == "INVITE":
                self.plugin.log_info(self._("Got invite to #{}").format(chan))

            else:
                self.plugin.log_info(
                    self._("PrivMsg: <{}> {}").format(sender_nick, text)
                )

            break

        else:
            self.plugin.log_warning(
                self._("'{}' did not respond to the request").format(bot)
            )

    @lock
    def is_bot_online(self, bot):
        self.plugin.log_info(self._("Checking if bot '{}' is online").format(bot))
        self.irc_sock.send("WHOIS {}\r\n".format(bot))

        start_time = time.time()
        while time.time() - start_time < 30:
            origin, command, args = self.get_irc_command()
            if (
                command == "401"
                and args[0] == self.nick
                and args[1].lower() == bot.lower()
            ):  #: ERR_NOSUCHNICK
                self.plugin.log_debug(f"Bot '{bot}' is offline")
                return False

            #: RPL_WHOISUSER
            elif (
                command == "311"
                and args[0] == self.nick
                and args[1].lower() == bot.lower()
            ):
                self.plugin.log_debug(f"Bot '{bot}' is online")
                self.bot_host[bot] = args[3]  #: bot host
                return True

            else:
                time.sleep(0.1)

        else:
            self.plugin.log_error(self._("Server did not respond in a reasonable time"))
            return False

    @lock
    def get_bot_host(self, bot):
        bot_host = self.bot_host.get(bot)
        if bot_host:
            return bot_host

        else:
            if self.is_bot_online(bot):
                return self.bot_host.get(bot)

            else:
                return None

    @lock
    def xdcc_request_pack(self, bot, pack):
        self.plugin.log_info(self._("Requesting pack #{}").format(pack))
        self.xdcc_request_time = time.time()
        self.irc_sock.send("PRIVMSG {} :xdcc send #{}\r\n".format(bot, pack))

    @lock
    def xdcc_cancel_pack(self, bot):
        if self.xdcc_request_time:
            self.plugin.log_info(self._("Requesting XDCC cancellation"))
            self.xdcc_request_time = None
            self.irc_sock.send("PRIVMSG {} :xdcc cancel\r\n".format(bot))

        else:
            self.plugin.log_warning(self._("No XDCC request pending, cannot cancel"))

    @lock
    def xdcc_request_resume(self, bot, dcc_port, file_name, resume_position):
        if self.xdcc_request_time:
            bot_host = self.get_bot_host(bot)

            self.plugin.log_info(
                self._("Requesting XDCC resume of '{}' at position {}").format(
                    file_name, resume_position
                )
            )

            self.irc_sock.send(
                'PRIVMSG {} :\x01DCC RESUME "{}" {} {}\x01\r\n'.format(
                    bot, os.fsdecode(file_name), dcc_port, resume_position
                )
            )

            start_time = time.time()
            while time.time() - start_time < 30:
                origin, command, args = self.get_irc_command()

                # Private message from bot to us?
                if (
                    origin
                    and command
                    and args
                    and "@" in origin
                    and (
                        origin[0 : len(bot)] == bot
                        or bot_host
                        and origin.split("@")[1] == bot_host
                    )
                    and args[0][0 : len(self.nick)] == self.nick
                    and command in ("PRIVMSG", "NOTICE")
                ):

                    try:
                        text = str(args[1], "utf-8")
                    except UnicodeDecodeError:
                        text = str(args[1], "latin1", "replace")

                    sender_nick = origin.split("@")[0].split("!")[0]
                    self.plugin.log_debug(
                        self._("PrivMsg: <{}> {}").format(sender_nick, text)
                    )

                    m = re.match(
                        r"\x01DCC ACCEPT .*? {} (?P<RESUME_POS>\d+)\x01".format(
                            dcc_port
                        ),
                        text,
                    )
                    if m:
                        self.plugin.log_debug(
                            self._(
                                "Bot '{}' acknowledged resume at position {}"
                            ).format(sender_nick, m.group("RESUME_POS"))
                        )
                        return int(m.group("RESUME_POS"))

                else:
                    time.sleep(0.1)

            self.plugin.log_warning(
                self._("Timeout while waiting for resume acknowledge, not resuming")
            )

        else:
            self.plugin.log_error(self._("No XDCC request pending, cannot resume"))

        return 0

    @lock
    def xdcc_get_pack_info(self, bot, pack):
        bot_host = self.get_bot_host(bot)

        self.plugin.log_info(self._("Requesting pack #{} info").format(pack))
        self.irc_sock.send("PRIVMSG {} :xdcc info #{}\r\n".format(bot, pack))

        info = {}
        start_time = time.time()
        while time.time() - start_time < 90:
            origin, command, args = self.get_irc_command()

            # Private message from bot to us?
            if (
                origin
                and command
                and args
                and (
                    origin[0 : len(bot)] == bot
                    or bot_host
                    and origin.split("@")[1] == bot_host
                )
                and args[0][0 : len(self.nick)] == self.nick
                and command in ("PRIVMSG", "NOTICE")
            ):

                try:
                    text = str(args[1], "utf-8")
                except UnicodeDecodeError:
                    text = str(args[1], "latin1", "replace")

                pack_info = text.split()
                if pack_info[0].lower() == "filename":
                    self.plugin.log_debug(f"Filename: '{pack_info[1]}'")
                    info.update({"status": "online", "name": pack_info[1]})

                elif pack_info[0].lower() == "filesize":
                    self.plugin.log_debug(f"Filesize: '{pack_info[1]}'")
                    info.update({"status": "online", "size": pack_info[1]})

                else:
                    sender_nick = origin.split("@")[0].split("!")[0]
                    self.plugin.log_debug(
                        self._("PrivMsg: <{}> {}").format(sender_nick, text)
                    )

            else:
                if len(info) > 2:  #: got both name and size
                    break

                time.sleep(0.1)

        else:
            if len(info) == 0:
                self.plugin.log_error(
                    self._("XDCC Bot '{}' did not answer").format(bot)
                )
                return {"status": "offline", "msg": "XDCC Bot did not answer"}

        return info


class XDCC(BaseDownloader):
    __name__ = "XDCC"
    __type__ = "downloader"
    __version__ = "0.48"
    __status__ = "testing"

    __pattern__ = (
        r"xdcc://(?P<SERVER>.*?)/#?(?P<CHAN>.*?)/(?P<BOT>.*?)/#?(?P<PACK>\d+)/?"
    )
    __config__ = [
        ("nick", "str", "Nickname", "pyload"),
        ("ident", "str", "Ident", "pyloadident"),
        ("realname", "str", "Realname", "pyloadreal"),
        ("try_resume", "bool", "Request XDCC resume?", True),
        ("nick_pw", "str", "Registered nickname password (optional)", ""),
        (
            "invite_opts",
            "str",
            "Invite bots options (format ircserver/channel/invitebot/password, ...)",
            "",
        ),
    ]

    __description__ = """Download from IRC XDCC bot"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def setup(self):
        self.dl_started = False
        self.dl_finished = False
        self.request_again = False

        self.irc_client = None
        self.exc_info = None

        self.dcc_port = 0
        self.dcc_file_name = ""
        self.dcc_sender_bot = None
        self.bot_host = None

        self.multi_dl = False

    def xdcc_send_resume(self, resume_position):
        if not self.config.get("try_resume") or not self.dcc_sender_bot:
            return 0

        else:
            return self.irc_client.xdcc_request_resume(
                self.dcc_sender_bot, self.dcc_port, self.dcc_file_name, resume_position
            )

    def process(self, pyfile):
        server = self.info["pattern"]["SERVER"]
        chan = self.info["pattern"]["CHAN"]
        bot = self.info["pattern"]["BOT"]
        pack = self.info["pattern"]["PACK"]

        temp = server.split(":")
        ln = len(temp)
        if ln == 2:
            host, port = temp[0], int(temp[1])

        elif ln == 1:
            host, port = temp[0], 6667

        else:
            self.fail(self._("Invalid hostname for IRC Server: {}").format(server))

        nick = self.config.get("nick")
        nick_pw = self.config.get("nick_pw")
        ident = self.config.get("ident")
        realname = self.config.get("realname")
        invite_opts = [
            x.split("/")
            for x in self.config.get("invite_opts").strip().split(",")
            if len(x.split("/")) == 4
        ]

        #: Remove leading '#' from channel name
        for opt in invite_opts:
            if opt[1].startswith("#"):
                opt[1] = opt[1][1:]

        #: Change request type
        self.req.close()
        self.req = self.pyload.request_factory.get_request(self.classname, type="XDCC")

        self.pyfile.set_custom_status("connect irc")

        self.irc_client = IRC(self, nick, ident, realname)
        for _ in range(3):
            try:
                if self.irc_client.connect_server(host, port):
                    try:
                        if nick_pw:
                            self.irc_client.nickserv_identify(nick_pw)

                        for opt in invite_opts:
                            if (
                                opt[0].lower() == host.lower()
                                and opt[1].lower() == chan.lower()
                            ):
                                self.irc_client.send_invite_request(
                                    opt[2], opt[1], opt[3]
                                )
                                break

                        if not self.irc_client.join_channel(chan):
                            self.fail(self._("Cannot join channel"))

                        if not self.irc_client.is_bot_online(bot):
                            self.fail(self._("Bot is offline"))

                        self.pyfile.set_status("waiting")

                        self.irc_client.xdcc_request_pack(bot, pack)

                        # Main IRC loop
                        while (
                            not self.pyfile.abort or self.dl_started
                        ) and not self.dl_finished:
                            if not self.dl_started:
                                if self.request_again:
                                    if (
                                        time.time() - self.irc_client.xdcc_request_time
                                        > 300
                                    ):
                                        self.irc_client.xdcc_request_pack(bot, pack)
                                        self.request_again = False

                                else:
                                    if (
                                        self.irc_client.xdcc_request_time
                                        and time.time()
                                        - self.irc_client.xdcc_request_time
                                        > 90
                                    ):
                                        self.irc_client.disconnect_server()
                                        self.log_error(
                                            self._("XDCC Bot did not answer")
                                        )
                                        self.retry(
                                            3, 60, self._("XDCC Bot did not answer")
                                        )

                            origin, command, args = self.irc_client.get_irc_command()
                            self.proccess_irc_command(origin, command, args)

                            if self.exc_info:
                                raise self.exc_info

                    finally:
                        self.irc_client.disconnect_server()

                return

            except socket.error as exc:
                if hasattr(exc, "errno") and exc.errno is not None:
                    err_no = exc.errno

                    if err_no in (10054, 10061):
                        self.log_warning("Server blocked our ip, retry in 5 min")
                        self.wait(300)
                        continue

                    else:
                        self.log_error(
                            self._("Failed due to socket errors. Code: {}").format(
                                err_no
                            )
                        )
                        self.fail(
                            self._("Failed due to socket errors. Code: {}").format(
                                err_no
                            )
                        )

                else:
                    err_msg = exc.args[0]
                    self.log_error(
                        self._("Failed due to socket errors: '{}'").format(err_msg)
                    )
                    self.fail(
                        self._("Failed due to socket errors: '{}'").format(err_msg)
                    )

        self.log_error(self._("Server blocked our ip, retry again later manually"))
        self.fail(self._("Server blocked our ip, retry again later manually"))

    def proccess_irc_command(self, origin, command, args):
        bot = self.info["pattern"]["BOT"]
        nick = self.config.get("nick")

        if origin is None or command is None or args is None:
            return

        # Private message from bot to us?
        bot_host = self.irc_client.get_bot_host(bot)
        if (
            "@" not in origin
            or (
                origin[0 : len(bot)] != bot
                and bot_host
                and origin.split("@")[1] != bot_host
            )
            or args[0][0 : len(nick)] != nick
            or command not in ("PRIVMSG", "NOTICE")
        ):
            return

        try:
            text = str(args[1], "utf-8")
        except UnicodeDecodeError:
            text = str(args[1], "latin1", "replace")

        sender_nick = origin.split("@")[0].split("!")[0]
        self.log_debug(f"PrivMsg: <{sender_nick}> {text}")

        if text in (
            "You already requested that pack",
            "All Slots Full",
            "You have a DCC pending",
        ):
            self.request_again = True

        elif "you must be on a known channel to request a pack" in text:
            self.log_error(self._("Invalid channel"))
            self.fail(self._("Invalid channel"))

        elif "Invalid Pack Number" in text:
            self.log_error(self._("Invalid Pack Number"))
            self.fail(self._("Invalid Pack Number"))

        m = re.match(
            r'\x01DCC SEND "?(?P<NAME>.*?)"? (?P<IP>\d+) (?P<PORT>\d+)(?: (?P<SIZE>\d+))?\x01',
            text,
        )  #: XDCC?
        if m:
            ip = socket.inet_ntoa(struct.pack("!I", int(m.group("IP"))))
            self.dcc_port = int(m.group("PORT"))
            self.dcc_file_name = m.group("NAME")
            self.dcc_sender_bot = origin.split("@")[0].split("!")[0]
            file_size = int(m.group("SIZE")) if m.group("SIZE") else 0

            self.do_download(ip, self.dcc_port, self.dcc_file_name, file_size)

    @threaded
    def do_download(self, ip, port, file_name, file_size):
        if self.dl_started:
            return

        self.dl_started = True

        try:
            self.pyfile.name = file_name
            self.req.filesize = file_size

            self.pyfile.set_status("downloading")

            dl_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                self.pyfile.package().folder
                if self.pyload.config.get("general", "folder_per_package")
                else "",
            )
            os.makedirs(dl_folder, exist_ok=True)
            self.set_permissions(dl_folder)

            self.check_duplicates()

            dl_file = os.path.join(dl_folder, self.pyfile.name)

            self.log_debug(
                self._("DOWNLOAD XDCC '{}' from {}:{}").format(file_name, ip, port)
            )

            self.pyload.addonManager.dispatchEvent(
                "download_start", self.pyfile, "{}:{}".format(ip, port), dl_file
            )

            newname = self.req.download(
                ip,
                port,
                dl_file,
                progressNotify=self.pyfile.set_progress,
                resume=self.xdcc_send_resume,
            )
            if newname and newname != dl_file:
                self.log_info(
                    self._("{name} saved as {newname}").format(
                        name=self.pyfile.name, newname=newname
                    )
                )
                dl_file = newname

            self.last_download = dl_file

        except Abort:
            pass

        except Exception as exc:
            bot = self.info["pattern"]["BOT"]
            self.irc_client.xdcc_cancel_pack(bot)

            if not self.exc_info:
                self.exc_info = sys.exc_info()  #: pass the exception to the main thread

        self.dl_finished = True
