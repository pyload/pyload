# -*- coding: utf-8 -*-

import sleekxmpp
from sleekxmpp.xmlstream.matcher import MatchXPath
from sleekxmpp.xmlstream.handler import Callback
import ssl

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
        ("maxline", "int", "Maximum line per message", 6)
    ]

    __description__ = """Connect to jabber and let owner perform different tasks"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]

    SHORTCUT_COMMANDS = {
        'a': 'add',
        'c': 'collector',
        'f': 'freeSpace',
        'h': 'help',
        'i': 'info',
        'l': 'getLog',
        'm': 'more',
        'p': 'packinfo',
        'q': 'queue',
        'r': 'restart',
        'rf': 'restartFile',
        'rp': 'restartPackage',
        's': 'status',
    }

    def __init__(self, *args, **kwargs):
        IRC.__init__(self, *args, **kwargs)

    def activate(self):
        self.log_debug('activate')
        self.new_package = {}
        self.jid = sleekxmpp.jid.JID(self.config.get('jid'))
        self.jid.resource = 'PyLoadNotifyBot'
        self.log_debug(self.jid)

        xmpp = NotifyBot(
            self.jid,
            self.config.get('pw'),
            self.config.get('tls'),
            self.config.get('use_ssl'),
            self.log_info,
            self.log_debug
        )
        self.log_debug('activate xmpp')
        xmpp.register_plugin('xep_0030')  # Service Discovery
        xmpp.register_plugin('xep_0004')  # Data Forms
        xmpp.register_plugin('xep_0060')  # PubSub
        xmpp.register_plugin('xep_0199')  # XMPP Ping
        xmpp.ssl_version = ssl.PROTOCOL_TLSv1_2

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        xmpp.add_event_handler("message", self.message)
        xmpp.add_event_handler("connected", self.connected)
        xmpp.add_event_handler("disconnected", self.disconnected)
        xmpp.add_event_handler("failed_auth", self.failed_auth)
        xmpp.add_event_handler("changed_status", self.changed_status)
        xmpp.add_event_handler("presence_error", self.presence_error)
        xmpp.add_event_handler("presence_unavailable",
                               self.presence_unavailable)

        xmpp.register_handler(Callback('Stream Error',
                                       MatchXPath("{%s}error" % xmpp.stream_ns),
                                       self.stream_error))

        self.xmpp = xmpp
        self.start()

    def run(self):
        self.log_debug('def run')
        try:
            if self.xmpp.connect():
                self.xmpp.process(block=False)
                self.log_info('Done')
                # self.periodical.start(30)

            else:
                self.log_error("Unable to connect.")

        except Exception as e:
            self.log_error(e, trace=True)

    ############################################################################
    ## xmpp handler

    def changed_status(self, stanza=None):
        self.log_debug('changed_status', stanza, stanza.get_type())

    def connected(self, event=None):
        self.log_info("Client was connected", event)

    def disconnected(self, event=None):
        self.log_info("Client was disconnected", event)

    def presence_error(self, stanza=None):
        self.log_debug('presence_error', stanza)

    def presence_unavailable(self, stanza=None):
        self.log_debug('presence_unavailable', stanza)

    def failed_auth(self, event=None):
        self.log_info('Failed to authenticate')

    def stream_error(self, err=None):
        self.log_debug("Stream Error", err)
        # self.periodical.stop()

    def message(self, stanza):
        """
        Message handler for the component.
        """
        self.log_debug('message', stanza)

        subject = stanza['subject']
        body = stanza['body']
        t = stanza['type']
        self.log_debug("Message from %s received." % stanza.get_from())
        self.log_debug("Body: %s Subject: %s Type: %s" % (body, subject, t))

        if t == "headline":
            #: 'headline' messages should never be replied to
            return True

        if subject:
            subject = "Re: " + subject

        to_jid = stanza["from"]
        from_jid = stanza["to"]
        to_name = to_jid.jid

        names = self.config.get("owners").split(";")

        self.log_debug("names", names)
        self.log_debug("to_name", to_name)
        self.log_debug("to_jid", to_jid)

        if not (to_name in names or to_jid.node + "@" + to_jid.domain in names):
            return True

        messages = []

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

        handler = getattr(self, "event_{}".format(trigger), self.event_pass)
        ret = False

        try:
            self.log_debug("args", args, type(args))

            res = handler(args)
            self.log_debug("res", res)

            if res:
                msg_reply = "\n".join(res)
                # add shortcut in help
                if command == "help":
                    msg_reply += "\nShortcut:\n"
                    for cmd_short, cmd_long in self.SHORTCUT_COMMANDS.items():
                        msg_reply += cmd_short + ": " + cmd_long + ", "

            else:
                msg_reply = "ERROR: command invalide, enter: help"

            self.log_debug('Send reponse', msg_reply)
            ret = stanza.reply(msg_reply).send()

        except Exception as exc:
            self.log_error(
                exc,
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

        return ret

    ## end xmpp handler
    ############################################################################

    def shortcut_command(self, shortcommand):
        command = shortcommand
        if shortcommand and shortcommand in self.SHORTCUT_COMMANDS:
            command = self.SHORTCUT_COMMANDS[shortcommand]

        return command

    def response(self, msg, origin=""):
        self.log_debug('def response', msg, origin)
        return self.announce(msg)

    def announce(self, message):
        """
        Send message to all owners
        """
        self.log_debug('Announce, message:', message)
        for user in self.config.get("owners").split(";"):
            self.log_debug("Send message to", user)
            to_jid = sleekxmpp.jid.JID(user)
            self.xmpp.sendMessage(
                mfrom=self.jid, mto=to_jid, mtype_type="chat", body=str(message)
            )

    def exit(self):
        self.xmpp.disconnect()

    def before_reconnect(self, ip):
        self.log_debug('after_reconnect')
        self.xmpp.disconnect()

    def after_reconnect(self, ip, oldip):
        self.log_debug('after_reconnect')
        self.xmpp.connect()
        # self.periodical.start(600)

    def download_failed(self, pyfile):
        self.log_debug("download_failed", pyfile, pyfile.error)
        try:
            if self.config.get("download_failed"):
                self.announce(self._("Download failed: {} (#{}) in #{} @ {}: {}").format(pyfile.name,
                                                                                pyfile.id,
                                                                                pyfile.packageid,
                                                                                pyfile.pluginname,
                                                                                pyfile.error))

        except Exception as exc:
            self.log_error(
                exc,
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

    def package_failed(self, pypack):
        self.log_debug("package_failed", pypack)
        try:
            if self.config.get("package_failed"):
                self.announce(self._("Package failed: {} ({}).").format(pypack.name, pypack.id))

        except Exception as e:
            self.log_error(e, trace=True)

    def package_finished(self, pypack):
        self.log_debug("package_finished")
        try:
            if self.config.get("info_pack"):
                self.announce(self._("Package finished: {} ({}).").format(pypack.name, pypack.id))

        except Exception as exc:
            self.log_error(
                exc,
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

    def download_finished(self, pyfile):
        self.log_debug("download_finished")
        try:
            if self.config.get("info_file"):
                self.announce(self._("Download finished: {} (#{}) in #{} @ {}").format(pyfile.name,
                                                                              pyfile.id,
                                                                              pyfile.packageid,
                                                                              pyfile.pluginname))

        except Exception as e:
            self.log_error(
                exc,
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )
    def all_downloads_processed(self, arg=None):
        self.log_debug('all_downloads_processed', arg)
        try:
            if self.config.get('all_download'):
                self.announce(_("All download finished."))

        except Exception:
            pass

    def download_start(self, pyfile, url, filename):
        self.log_debug('download_start', pyfile, url, filename)
        try:
            if self.config.get('download_start'):
                self.announce(_("Download start: %s (#%d) in (#%d) @ %s.") % (pyfile.name,
                                                                              pyfile.id,
                                                                              pyfile.packageid,
                                                                              pyfile.pluginname))
        except Exception:
            pass

class NotifyBot(sleekxmpp.ClientXMPP):
    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.
    """

    def __init__(self, jid, password, use_tls, use_ssl, log_info, log_debug):
        self.log_debug = log_debug
        self.log_info = log_info

        sleekxmpp.ClientXMPP.__init__(self, jid, password, use_tls=use_tls, use_ssl=use_ssl)
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.log_debug("start")
        self.send_presence()
        self.get_roster(timeout=60)
