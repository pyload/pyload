# -*- coding: utf-8 -*-

import socket
import time

try:
    import ssl
except ImportError:
    pass

from module.plugins.internal.Addon import Addon, threaded
from module.plugins.internal.misc import forward, lock


#@TODO: IPv6 support
class ClickNLoad(Addon):
    __name__    = "ClickNLoad"
    __type__    = "hook"
    __version__ = "0.53"
    __status__  = "testing"

    __config__ = [("activated", "bool"           , "Activated"                      , True       ),
                  ("port"     , "int"            , "Port"                           , 9666       ),
                  ("extern"   , "bool"           , "Listen for external connections", True       ),
                  ("dest"     , "queue;collector", "Add packages to"                , "collector")]

    __description__ = """Click'n'Load support"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.de"           ),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de"     , "nitzo2001[AT]yahoo[DOT]com")]


    def activate(self):
        if not self.pyload.config.get('webinterface', 'activated'):
            return

        cnlip   = "" if self.config.get('extern') else "127.0.0.1"
        cnlport = self.config.get('port')
        webip   = "127.0.0.1" if any(_ip == self.pyload.config.get('webinterface', 'host') for _ip in ("0.0.0.0", "")) \
            else self.pyload.config.get('webinterface', 'host')
        webport = self.pyload.config.get('webinterface', 'port')

        self.pyload.scheduler.addJob(5, self.proxy, [cnlip, cnlport, webip, webport], threaded=False)


    @lock
    @threaded
    def forward(self, source, destination, queue=False):
        if queue:
            old_ids = set(pack.id for pack in self.pyload.api.getCollector())

        forward(source, destination)

        if queue:
            new_ids = set(pack.id for pack in self.pyload.api.getCollector())
            for id in new_ids - old_ids:
                self.pyload.api.pushToQueue(id)


    @threaded
    def proxy(self, cnlip, cnlport, webip, webport):
        self.log_info(_("Proxy listening on %s:%s") % (cnlip or "0.0.0.0", cnlport))
        self._server(cnlip, cnlport, webip, webport)


    @threaded
    def _server(self, cnlip, cnlport, webip, webport):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind((cnlip, cnlport))
            dock_socket.listen(5)

            while True:
                client_socket, client_addr = dock_socket.accept()
                self.log_debug("Connection from %s:%s" % client_addr)

                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                if self.pyload.config.get('webinterface', 'https'):
                    try:
                        server_socket = ssl.wrap_socket(server_socket)

                    except NameError:
                        self.log_error(_("Missing SSL lib"), _("Please disable HTTPS in pyLoad settings"))
                        client_socket.close()
                        continue

                    except Exception, e:
                        self.log_error(_("SSL error: %s") % e.message)
                        client_socket.close()
                        continue

                server_socket.connect((webip, webport))

                self.forward(client_socket, server_socket, self.config.get('dest') == "queue")
                self.forward(server_socket, client_socket)

        except socket.timeout:
            self.log_debug("Connection timed out, retrying...")
            return self._server(cnlip, cnlport, webip, webport)

        except socket.error, e:
            self.log_error(e)
            time.sleep(240)
            return self._server(cnlip, cnlport, webip, webport)
