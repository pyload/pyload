# -*- coding: utf-8 -*-

import pyxmpp
import pyxmpp.all
import pyxmpp.interfaces
from pyxmpp.jabber.client import JabberClient

from .IRC import IRC


class XMPP(IRC, JabberClient):
    __name__ = "XMPP"
    __type__ = "hook"
    __version__ = "0.18"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("jid", "str", "Jabber ID", "user@exmaple-jabber-server.org"),
                  ("pw", "str", "Password", ""),
                  ("tls", "bool", "Use TLS", False),
                  ("owners", "str", "List of JIDs accepting commands from",
                   "me@icq-gateway.org;some@msn-gateway.org"),
                  ("keepalive", "int", "Keepalive interval in seconds (0 to disable)", 0),
                  ("info_file", "bool", "Inform about every file finished", False),
                  ("info_pack", "bool", "Inform about every package finished", True),
                  ("captcha", "bool", "Send captcha requests", True)]

    __description__ = """Connect to jabber and let owner perform different tasks"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.org")]

    pyxmpp.interface.implements(pyxmpp.interfaces.IMessageHandlersProvider)

    def __init__(self, *args, **kwargs):
        IRC.__init__(self, *args, **kwargs)

        self.jid = pyxmpp.all.JID(self.config.get('jid'))
        password = self.config.get('pw')

        #: If bare JID is provided add a resource -- it is required
        if not self.jid.resource:
            self.jid = pyxmpp.all.JID(self.jid.node, self.jid.domain, "pyLoad")

        if self.config.get('tls'):
            tls_settings = pyxmpp.streamtls.TLSSettings(
                require=True, verify_peer=False)
            auth = ("sasl:PLAIN", "sasl:DIGEST-MD5")
        else:
            tls_settings = None
            auth = ("sasl:DIGEST-MD5", "digest")

        #: Setup client with provided connection information
        #: And identity data
        JabberClient.__init__(self, self.jid, password,
                              disco_name="pyLoad XMPP Client", disco_type="bot",
                              tls_settings=tls_settings, auth_methods=auth, keepalive=self.config.get('keepalive'))

        self.interface_providers = [
            VersionHandler(self),
            self,
        ]

    def activate(self):
        self.new_package = {}

        self.start()

    def package_finished(self, pypack):
        try:
            if self.config.get('info_pack'):
                self.announce(_("Package finished: %s") % pypack.name)

        except Exception:
            pass

    def download_finished(self, pyfile):
        try:
            if self.config.get('info_file'):
                self.announce(
                    _("Download finished: %(name)s @ %(plugin)s") % {'name': pyfile.name, 'plugin': pyfile.pluginname})

        except Exception:
            pass

    def run(self):
        #: Connect to IRC etc.
        self.connect()
        try:
            self.loop()

        except Exception, ex:
            self.log_error(ex)

    def stream_state_changed(self, state, arg):
        """
        This one is called when the state of stream connecting the component
        to a server changes. This will usually be used to let the user
        know what is going on.
        """
        self.log_debug("*** State changed: %s %r ***" % (state, arg))

    def disconnected(self):
        self.log_debug("Client was disconnected")

    def stream_closed(self, stream):
        self.log_debug("Stream was closed", stream)

    def stream_error(self, err):
        self.log_debug("Stream Error", err)

    def get_message_handlers(self):
        """
        Return list of (message_type, message_handler) tuples.

        The handlers returned will be called when matching message is received
        in a client session.
        """
        return [("normal", self.message)]

    def message(self, stanza):
        """
        Message handler for the component.
        """
        subject = stanza.get_subject()
        body = stanza.get_body()
        t = stanza.get_type()
        self.log_debug("Message from %s received." % stanza.get_from())
        self.log_debug("Body: %s Subject: %s Type: %s" % (body, subject, t))

        if t == "headline":
            #: 'headline' messages should never be replied to
            return True
        if subject:
            subject = u"Re: " + subject

        to_jid = stanza.get_from()
        from_jid = stanza.get_to()

        # j = pyxmpp.all.JID()
        to_name = to_jid.as_utf8()

        names = self.config.get('owners').split(";")

        if to_name in names or to_jid.node + "@" + to_jid.domain in names:
            messages = []

            trigger = "pass"
            args = None

            try:
                temp = body.split()
                trigger = temp[0]
                if len(temp) > 1:
                    args = temp[1:]

            except Exception:
                pass

            handler = getattr(self, "event_%s" % trigger, self.event_pass)
            try:
                res = handler(args)
                for line in res:
                    m = pyxmpp.all.Message(
                        to_jid=to_jid,
                        from_jid=from_jid,
                        stanza_type=stanza.get_type(),
                        subject=subject,
                        body=line)

                    messages.append(m)

            except Exception, e:
                self.log_error(e, trace=True)

            return messages

        else:
            return True

    def response(self, msg, origin=""):
        return self.announce(msg)

    def announce(self, message):
        """
        Send message to all owners
        """
        for user in self.config.get('owners').split(";"):
            self.log_debug("Send message to", user)

            to_jid = pyxmpp.all.JID(user)

            m = pyxmpp.all.Message(from_jid=self.jid,
                                   to_jid=to_jid,
                                   stanza_type="chat",
                                   body=message)

            stream = self.get_stream()
            if not stream:
                self.connect()
                stream = self.get_stream()

            stream.send(m)

    def before_reconnect(self, ip):
        self.disconnect()

    def after_reconnect(self, ip, oldip):
        self.connect()


class VersionHandler(object):
    """
    Provides handler for a version query.

    This class will answer version query and announce 'jabber:iq:version' namespace
    in the client's disco#info results.
    """
    pyxmpp.interface.implements(
        pyxmpp.interfaces.IIqHandlersProvider,
        pyxmpp.interfaces.IFeaturesProvider)

    def __init__(self, client):
        """
        Just remember who created this.
        """
        self.client = client

    def get_features(self):
        """
        Return namespace which should the client include in its reply to a
        disco#info query.
        """
        return ["jabber:iq:version"]

    def get_iq_get_handlers(self):
        """
        Return list of tuples (element_name, namespace, handler) describing
        handlers of <iq type='get'/> stanzas
        """
        return [("query", "jabber:iq:version", self.get_version)]

    def get_iq_set_handlers(self):
        """
        Return empty list, as this class provides no <iq type='set'/> stanza handler.
        """
        return []

    def get_version(self, iq):
        """
        Handler for jabber:iq:version queries.

        jabber:iq:version queries are not supported directly by PyXMPP, so the
        XML node is accessed directly through the libxml2 API.  This should be
        used very carefully!
        """
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:version")
        q.newTextChild(q.ns(), "name", "Echo component")
        q.newTextChild(q.ns(), "version", "1.0")
        return iq
