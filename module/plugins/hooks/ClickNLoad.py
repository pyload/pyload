# -*- coding: utf-8 -*-

import socket
import time

try:
    import ssl
except ImportError:
    pass

from threading import Lock

from module.plugins.internal.Addon import Addon, threaded


def forward(source, destination):
    try:
        bufsize = 1024
        bufdata = source.recv(bufsize)
        while bufdata:
            destination.sendall(bufdata)
            bufdata = source.recv(bufsize)
    finally:
        destination.shutdown(socket.SHUT_WR)
        #: destination.close()


#@TODO: IPv6 support
class ClickNLoad(Addon):
    __name__    = "ClickNLoad"
    __type__    = "hook"
    __version__ = "0.48"
    __status__  = "testing"

    __config__ = [("activated", "bool"           , "Activated"                      , True       ),
                  ("port"     , "int"            , "Port"                           , 9666       ),
                  ("extern"   , "bool"           , "Listen for external connections", True       ),
                  ("dest"     , "queue;collector", "Add packages to"                , "collector")]

    __description__ = """Click'n'Load support"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.de"  ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def activate(self):
        if not self.pyload.config.get("webinterface", "activated"):
            return

        ip      = "" if self.get_config('extern') else "127.0.0.1"
        webport = self.pyload.config.get("webinterface", "port")
        cnlport = self.get_config('port')

        self.proxy(ip, webport, cnlport)


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
    def proxy(self, ip, webport, cnlport):
        time.sleep(10)  #@TODO: Remove in 0.4.10 (implement addon delay on startup)

        self.log_info(_("Proxy listening on %s:%s") % (ip or "0.0.0.0", cnlport))

        self._server(ip, webport, cnlport)

        lock = Lock()
        lock.acquire()
        lock.acquire()


    @threaded
    def _server(self, ip, webport, cnlport):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind((ip, cnlport))
            dock_socket.listen(5)

            while True:
                client_socket, client_addr = dock_socket.accept()
                self.log_debug("Connection from %s:%s" % client_addr)

                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                if self.pyload.config.get("webinterface", "https"):
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

                server_socket.connect(("127.0.0.1", webport))

                self.forward(client_socket, server_socket, self.get_config('dest') is "queue")
                self.forward(server_socket, client_socket)

        except socket.timeout:
            self.log_debug("Connection timed out, retrying...")
            return self._server(ip, webport, cnlport)

        except socket.error, e:
            self.log_error(e)
            time.sleep(240)
            return self._server(ip, webport, cnlport)
