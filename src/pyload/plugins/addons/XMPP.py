# -*- coding: utf-8 -*-

import asyncio
import ssl

import slixmpp
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXPath

from .IRC import IRC


class XMPP(IRC):
    __name__ = "XMPP"
    __type__ = "addon"
    __version__ = "0.22"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("jid", "str", "Jabber ID", "user@exmaple-jabber-server.org"),
        ("pw", "str", "Password", ""),
        ("use_ipv6", "bool", "Use ipv6", False),
        ("tls", "bool", "Use TLS", True),
        ("use_ssl", "bool", "Use old SSL", False),
        (
            "owners",
            "str",
            "List of JIDs accepting commands from",
            "me@icq-gateway.org;some@msn-gateway.org",
        ),
        ("captcha", "bool", "Send captcha requests", True),
        ("info_file", "bool", "Inform about every file finished", False),
        ("info_pack", "bool", "Inform about every package finished", True),
        ("all_download", "bool", "Inform about all download finished", False),
        ("package_failed", "bool", "Notify package failed", False),
        ("download_failed", "bool", "Notify download failed", True),
        ("download_start", "bool", "Notify download start", True),
        ("maxline", "int", "Maximum line per message", 6),
    ]

    __description__ = """Connect to jabber and let owner perform different tasks"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    SHORTCUT_COMMANDS = {
        "a": "add",
        "c": "collector",
        "f": "freespace",
        "h": "help",
        "i": "info",
        "l": "getLog",
        "m": "more",
        "p": "packinfo",
        "q": "queue",
        "r": "restart",
        "rf": "restartfile",
        "rp": "restartpackage",
        "s": "status",
    }

    def __init__(self, *args, **kwargs):
        IRC.__init__(self, *args, **kwargs)

    def activate(self):
        self.log_debug("activate")
        self.jid = slixmpp.jid.JID(self.config.get("jid"))
        self.jid.resource = "PyLoadNotifyBot"
        self.log_debug(self.jid)

        self.start()

    def run(self):
        self.log_debug("def run")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        xmpp = NotifyBot(
            self.jid,
            self.config.get("pw"),
            self.log_info,
            self.log_debug,
        )
        self.log_debug("activate xmpp")
        xmpp.use_ipv6 = self.config.get("use_ipv6")
        xmpp.register_plugin("xep_0030")  # Service Discovery
        xmpp.register_plugin("xep_0004")  # Data Forms
        xmpp.register_plugin("xep_0060")  # PubSub
        xmpp.register_plugin("xep_0199")  # XMPP Ping
        xmpp.ssl_version = ssl.PROTOCOL_TLSv1_2

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        xmpp.add_event_handler("message", self.message)
        xmpp.add_event_handler("connected", self.connected)
        xmpp.add_event_handler("connection_failed", self.connection_failed)
        xmpp.add_event_handler("disconnected", self.disconnected)
        xmpp.add_event_handler("failed_auth", self.failed_auth)
        xmpp.add_event_handler("changed_status", self.changed_status)
        xmpp.add_event_handler("presence_error", self.presence_error)
        xmpp.add_event_handler("presence_unavailable", self.presence_unavailable)

        xmpp.register_handler(
            Callback(
                "Stream Error",
                MatchXPath(f"{{{xmpp.stream_ns}}}error"),
                self.stream_error,
            )
        )

        self.xmpp = xmpp
        self.xmpp.connect(
            use_ssl=self.config.get("use_ssl"),
            force_starttls=self.config.get("tls"),
        )
        self.xmpp.process(forever=True)

    ############################################################################
    # xmpp handlers

    def changed_status(self, stanza=None):
        self.log_debug("changed_status", stanza, stanza.get_type())

    def connection_failed(self, stanza=None):
        self.log_error("Unable to connect", stanza)

    def connected(self, event=None):
        self.log_info("Client was connected", event)

    def disconnected(self, event=None):
        self.log_info("Client was disconnected", event)

    def presence_error(self, stanza=None):
        self.log_debug("presence_error", stanza)

    def presence_unavailable(self, stanza=None):
        self.log_debug("presence_unavailable", stanza)

    def failed_auth(self, event=None):
        self.log_info("Failed to authenticate")

    def stream_error(self, err=None):
        self.log_debug("Stream Error", err)
        # self.periodical.stop()

    def message(self, stanza):
        """
        Message handler for the component.
        """
        self.log_debug("message", stanza)

        subject = stanza["subject"]
        body = stanza["body"]
        msg_type = stanza["type"]
        sender_jid = stanza["from"]
        names = self.config.get("owners").split(";")

        self.log_debug(f"Message from {sender_jid} received.")
        self.log_debug(f"Body: {body} Subject: {subject} Type: {msg_type}")

        if msg_type == "headline":
            #: 'headline' messages should never be replied to
            return True

        if subject:
            subject = "Re: " + subject

        if not (sender_jid.username in names or sender_jid.bare in names):
            return True

        command = "pass"
        args = None

        try:
            temp = body.split()
            command = temp[0]
            if len(temp) > 1:
                args = temp[1:]

        except Exception:
            pass

        self.log_debug("command", command)
        command = self.shortcut_command(command)
        self.log_debug("shortcut_command", command)

        handler = getattr(self, f"event_{command}", self.event_pass)
        ret = False
        try:
            self.log_debug("args", args, type(args))

            res = handler(args)
            self.log_debug("res", res)

            if res:
                msg_reply = "\n".join(res)
                # add shortcut in help
                if command == "help":
                    msg_reply += "\nShortcuts:\n"
                    for cmd_short, cmd_long in self.SHORTCUT_COMMANDS.items():
                        msg_reply += cmd_short + ": " + cmd_long + ", "

            else:
                msg_reply = "ERROR: invalid command, enter: help"

            self.log_debug("Send response", msg_reply)
            ret = stanza.reply(msg_reply).send()

        except Exception as exc:
            self.log_error(exc)
            stanza.reply("ERROR: " + str(exc)).send()

        return ret

    # end xmpp handler
    ############################################################################

    def shortcut_command(self, shortcommand):
        if shortcommand and shortcommand in self.SHORTCUT_COMMANDS:
            command = self.SHORTCUT_COMMANDS[shortcommand]
        else:
            command = shortcommand

        return command

    def announce(self, message):
        """
        Send message to all owners
        """
        self.log_debug("Announce, message:", message)
        for user in self.config.get("owners").split(";"):
            self.log_debug("Send message to", user)
            to_jid = slixmpp.jid.JID(user)
            self.xmpp.sendMessage(
                mfrom=self.jid, mto=to_jid, mtype="chat", mbody=str(message)
            )

    ############################################################################
    # pyLoad events

    def exit(self):
        self.xmpp.disconnect()

    def before_reconnect(self, ip):
        self.log_debug("before_reconnect")
        self.xmpp.disconnect()

    def after_reconnect(self, ip, oldip):
        self.log_debug("after_reconnect")
        self.xmpp.connect()
        # self.periodical.start(600)

    def download_failed(self, pyfile):
        self.log_debug("download_failed", pyfile, pyfile.error)
        try:
            if self.config.get("download_failed"):
                self.announce(
                    self._("Download failed: {} (#{}) in #{} @ {}: {}").format(
                        pyfile.name,
                        pyfile.id,
                        pyfile.packageid,
                        pyfile.pluginname,
                        pyfile.error,
                    )
                )

        except Exception as exc:
            self.log_error(exc)

    def package_failed(self, pypack):
        self.log_debug("package_failed", pypack)
        try:
            if self.config.get("package_failed"):
                self.announce(
                    self._("Package failed: {} ({}).").format(pypack.name, pypack.id)
                )

        except Exception as exc:
            self.log_error(exc)

    def package_finished(self, pypack):
        self.log_debug("package_finished")
        try:
            if self.config.get("info_pack"):
                self.announce(
                    self._("Package finished: {} ({}).").format(pypack.name, pypack.id)
                )

        except Exception as exc:
            self.log_error(exc)

    def download_finished(self, pyfile):
        self.log_debug("download_finished")
        try:
            if self.config.get("info_file"):
                self.announce(
                    self._("Download finished: {} (#{}) in #{} @ {}").format(
                        pyfile.name, pyfile.id, pyfile.packageid, pyfile.pluginname
                    )
                )

        except Exception as exc:
            self.log_error(exc)

    def all_downloads_processed(self, arg=None):
        self.log_debug("all_downloads_processed", arg)
        try:
            if self.config.get("all_download"):
                self.announce(self._("All download finished."))

        except Exception:
            pass

    def download_start(self, pyfile, url, filename):
        self.log_debug("download_start", pyfile, url, filename)
        try:
            if self.config.get("download_start"):
                self.announce(
                    self._("Download start: {} (#{}) in (#{}) @ {}.").format(
                        pyfile.name, pyfile.id, pyfile.packageid, pyfile.pluginname
                    )
                )
        except Exception:
            pass

    # end pyLoad events
    ############################################################################


class NotifyBot(slixmpp.ClientXMPP):
    def __init__(self, jid, password, log_info, log_debug):
        self.log_debug = log_debug
        self.log_info = log_info

        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.log_debug("Session started")
        self.send_presence()
        self.get_roster(timeout=60)
