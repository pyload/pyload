# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
    
    @author: RaNaN
    @interface-version: 0.2
"""

from pyxmpp import streamtls
from pyxmpp.all import JID, Message, Presence
from pyxmpp.jabber.client import JabberClient
from pyxmpp.interface import implements
from pyxmpp.interfaces import *

from module.plugins.addons.IRCInterface import IRCInterface

class XMPPInterface(IRCInterface, JabberClient):
    __name__ = "XMPPInterface"
    __version__ = "0.1"
    __description__ = """connect to jabber and let owner perform different tasks"""
    __config__ = [("activated", "bool", "Activated", "False"),
            ("jid", "str", "Jabber ID", "user@exmaple-jabber-server.org"),
            ("pw", "str", "Password", ""),
            ("tls", "bool", "Use TLS", False),
            ("owners", "str", "List of JIDs accepting commands from", "me@icq-gateway.org;some@msn-gateway.org"),
            ("info_file", "bool", "Inform about every file finished", "False"),
            ("info_pack", "bool", "Inform about every package finished", "True"),
            ("captcha", "bool", "Send captcha requests", "True")]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    implements(IMessageHandlersProvider)

    def __init__(self, core, manager):
        IRCInterface.__init__(self, core, manager)

        self.jid = JID(self.getConfig("jid"))
        password = self.getConfig("pw")

        # if bare JID is provided add a resource -- it is required
        if not self.jid.resource:
            self.jid = JID(self.jid.node, self.jid.domain, "pyLoad")

        if self.getConfig("tls"):
            tls_settings = streamtls.TLSSettings(require=True, verify_peer=False)
            auth = ("sasl:PLAIN", "sasl:DIGEST-MD5")
        else:
            tls_settings = None
            auth = ("sasl:DIGEST-MD5", "digest")

        # setup client with provided connection information
        # and identity data
        JabberClient.__init__(self, self.jid, password,
                              disco_name="pyLoad XMPP Client", disco_type="bot",
                              tls_settings=tls_settings, auth_methods=auth)

        self.interface_providers = [
            VersionHandler(self),
            self,
            ]

    def coreReady(self):
        self.new_package = {}

        self.start()

    def packageFinished(self, pypack):
        try:
            if self.getConfig("info_pack"):
                self.announce(_("Package finished: %s") % pypack.name)
        except:
            pass

    def downloadFinished(self, pyfile):
        try:
            if self.getConfig("info_file"):
                self.announce(
                    _("Download finished: %(name)s @ %(plugin)s") % {"name": pyfile.name, "plugin": pyfile.pluginname})
        except:
            pass

    def run(self):
        # connect to IRC etc.
        self.connect()
        try:
            self.loop()
        except Exception, ex:
            self.core.log.error("pyLoad XMPP: %s" % str(ex))

    def stream_state_changed(self, state, arg):
        """This one is called when the state of stream connecting the component
        to a server changes. This will usually be used to let the user
        know what is going on."""
        self.log.debug("pyLoad XMPP: *** State changed: %s %r ***" % (state, arg))

    def disconnected(self):
        self.log.debug("pyLoad XMPP: Client was disconnected")

    def stream_closed(self, stream):
        self.log.debug("pyLoad XMPP: Stream was closed | %s" % stream)

    def stream_error(self, err):
        self.log.debug("pyLoad XMPP: Stream Error: %s" % err)

    def get_message_handlers(self):
        """Return list of (message_type, message_handler) tuples.

        The handlers returned will be called when matching message is received
        in a client session."""
        return [
                ("normal", self.message),
                ]

    def presence_control(self, stanza):
        from_jid = unicode(stanza.get_from_jid())
        stanza_type = stanza.get_type()
        self.log.debug("pyLoad XMPP: %s stanza from %s" % (stanza_type,
            from_jid))

        if from_jid in self.getConfig("owners"):
            return stanza.make_accept_response()

        return stanza.make_deny_response()

    def session_started(self):
        self.stream.send(Presence())

        self.stream.set_presence_handler("subscribe", self.presence_control)
        self.stream.set_presence_handler("subscribed", self.presence_control)
        self.stream.set_presence_handler("unsubscribe", self.presence_control)
        self.stream.set_presence_handler("unsubscribed", self.presence_control)

    def message(self, stanza):
        """Message handler for the component."""
        subject = stanza.get_subject()
        body = stanza.get_body()
        t = stanza.get_type()
        self.log.debug(u'pyLoad XMPP: Message from %s received.' % (unicode(stanza.get_from(), )))
        self.log.debug(u'pyLoad XMPP: Body: %s Subject: %s Type: %s' % (body, subject, t))

        if t == "headline":
            # 'headline' messages should never be replied to
            return True
        if subject:
            subject = u"Re: " + subject

        to_jid = stanza.get_from()
        from_jid = stanza.get_to()

        #j = JID()
        to_name = to_jid.as_utf8()
        from_name = from_jid.as_utf8()

        names = self.getConfig("owners").split(";")

        if to_name in names or to_jid.node + "@" + to_jid.domain in names:
            messages = []

            trigger = "pass"
            args = None

            try:
                temp = body.split()
                trigger = temp[0]
                if len(temp) > 1:
                    args = temp[1:]
            except:
                pass

            handler = getattr(self, "event_%s" % trigger, self.event_pass)
            try:
                res = handler(args)
                for line in res:
                    m = Message(
                        to_jid=to_jid,
                        from_jid=from_jid,
                        stanza_type=stanza.get_type(),
                        subject=subject,
                        body=line)

                    messages.append(m)
            except Exception, e:
                self.log.error("pyLoad XMPP: " + repr(e))

            return messages

        else:
            return True

    def response(self, msg, origin=""):
        return self.announce(msg)

    def announce(self, message):
        """ send message to all owners"""
        for user in self.getConfig("owners").split(";"):
            self.log.debug("pyLoad XMPP: Send message to %s" % user)

            to_jid = JID(user)

            m = Message(from_jid=self.jid,
                        to_jid=to_jid,
                        stanza_type="chat",
                        body=message)

            stream = self.get_stream()
            if not stream:
                self.connect()
                stream = self.get_stream()

            stream.send(m)

    def beforeReconnecting(self, ip):
        self.disconnect()

    def afterReconnecting(self, ip):
        self.connect()


class VersionHandler(object):
    """Provides handler for a version query.
    
    This class will answer version query and announce 'jabber:iq:version' namespace
    in the client's disco#info results."""

    implements(IIqHandlersProvider, IFeaturesProvider)

    def __init__(self, client):
        """Just remember who created this."""
        self.client = client

    def get_features(self):
        """Return namespace which should the client include in its reply to a
        disco#info query."""
        return ["jabber:iq:version"]

    def get_iq_get_handlers(self):
        """Return list of tuples (element_name, namespace, handler) describing
        handlers of <iq type='get'/> stanzas"""
        return [
                ("query", "jabber:iq:version", self.get_version),
                                                                ]

    def get_iq_set_handlers(self):
        """Return empty list, as this class provides no <iq type='set'/> stanza handler."""
        return []

    def get_version(self, iq):
        """Handler for jabber:iq:version queries.

        jabber:iq:version queries are not supported directly by PyXMPP, so the
        XML node is accessed directly through the libxml2 API.  This should be
        used very carefully!"""
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:version")
        q.newTextChild(q.ns(), "name", "Echo component")
        q.newTextChild(q.ns(), "version", "1.0")
        return iq

    def unload(self):
        self.log.debug("pyLoad XMPP: unloading")
        self.disconnect()

    def deactivate(self):
        self.unload()
