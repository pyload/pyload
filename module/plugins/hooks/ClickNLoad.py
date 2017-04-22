# -*- coding: utf-8 -*-

import socket
import threading
import time

from ..internal.Addon import Addon
from ..internal.misc import forward, lock, threaded

try:
    import ssl
except ImportError:
    pass


#@TODO: IPv6 support
class ClickNLoad(Addon):
    __name__ = "ClickNLoad"
    __type__ = "hook"
    __version__ = "0.61"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", True),
                  ("port", "int", "Port", 9666),
                  ("extern", "bool", "Listen for external connections", True),
                  ("dest", "queue;collector", "Add packages to", "collector")]

    __description__ = """Click'n'Load support"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.de"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def init(self):
        self.cnl_ip = "" if self.config.get('extern') else "127.0.0.1"
        self.cnl_port = self.config.get('port')
        self.web_ip    = "127.0.0.1" if any(_ip == self.pyload.config.get('webinterface', 'host') for _ip in ("0.0.0.0", "")) \
            else self.pyload.config.get('webinterface', 'host')
        self.web_port = self.pyload.config.get('webinterface', 'port')

        self.server_running = False
        self.do_exit = False
        self.exit_done = threading.Event()

    def activate(self):
        if not self.pyload.config.get('webinterface', 'activated'):
            self.log_warning(
                _("pyLoad's Web interface is not active, ClickNLoad cannot start"))
            return

        self.pyload.scheduler.addJob(5, self.proxy, threaded=False)

    def deactivate(self):
        if self.server_running:
            self.log_info(_("Shutting down proxy..."))

            self.do_exit = True

            try:
                wakeup_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                wakeup_socket.connect(
                    ("127.0.0.1" if any(
                        _ip == self.cnl_ip for _ip in (
                            "0.0.0.0",
                            "")) else self.cnl_ip,
                        self.cnl_port))
                wakeup_socket.close()
            except Exception:
                pass

            self.exit_done.wait(10)
            if self.exit_done.isSet():
                self.log_debug("Server exited successfully")
            else:
                self.log_warning(
                    _("Server was not exited gracefully, shutdown forced"))

    @lock
    @threaded
    def forward(self, source, destination, queue=False):
        if queue:
            old_ids = set(pack.pid for pack in self.pyload.api.getCollector())

        forward(source, destination)

        if queue:
            new_ids = set(pack.pid for pack in self.pyload.api.getCollector())
            for id in new_ids - old_ids:
                self.pyload.api.pushToQueue(id)

    @threaded
    def proxy(self):
        self.log_info(
            _("Proxy listening on %s:%s") %
            (self.cnl_ip or "0.0.0.0", self.cnl_port))
        self._server()

    @threaded
    def _server(self):
        try:
            self.exit_done.clear()
            self.server_running = True

            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            dock_socket.bind((self.cnl_ip, self.cnl_port))
            dock_socket.listen(5)

            while True:
                client_socket, client_addr = dock_socket.accept()

                if not self.do_exit:
                    self.log_debug("Connection from %s:%s" % client_addr)

                    server_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)

                    if self.pyload.config.get('webinterface', 'https'):
                        try:
                            server_socket = ssl.wrap_socket(server_socket)

                        except NameError:
                            self.log_error(
                                _("Missing SSL lib"),
                                _("Please disable HTTPS in pyLoad settings"))
                            client_socket.close()
                            continue

                        except Exception, e:
                            self.log_error(_("SSL error: %s") % e.message)
                            client_socket.close()
                            continue

                    server_socket.connect((self.web_ip, self.web_port))

                    self.forward(
                        client_socket,
                        server_socket,
                        self.config.get('dest') == "queue")
                    self.forward(server_socket, client_socket)

                else:
                    break

            dock_socket.close()
            self.server_running = False
            self.exit_done.set()

        except socket.timeout:
            self.log_debug("Connection timed out, retrying...")
            return self._server()

        except socket.error, e:
            self.log_error(e)
            time.sleep(240)
            return self._server()
