# -*- coding: utf-8 -*-

import socket
import ssl
import threading
import time

from pyload.core.utils.struct.lock import lock

from ..base.addon import BaseAddon, threaded
from ..helpers import forward


# TODO: IPv6 support
class ClickNLoad(BaseAddon):
    __name__ = "ClickNLoad"
    __type__ = "addon"
    __version__ = "0.62"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("port", "int", "Port", 9666),
        ("extern", "bool", "Listen for external connections", True),
        ("dest", "queue;collector", "Add packages to", "collector"),
    ]

    __description__ = """Click'n'Load support"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def init(self):
        self.cnl_ip = "" if self.config.get("extern") else "127.0.0.1"
        self.cnl_port = self.config.get("port")

        self.server_running = False
        self.do_exit = False
        self.exit_done = threading.Event()
        self.backend_found = threading.Event()

        self.pyload.scheduler.add_job(5, self._find_backend, threaded=False)

    @threaded
    def _find_backend(self):
        if self.pyload.config.get("webui", "enabled"):
            web_host = self.pyload.config.get("webui", "host")
            web_port = self.pyload.config.get("webui", "port")
            if web_host in ("0.0.0.0", "::"):
                web_host = "127.0.0.1"

            try:
                addrinfo = socket.getaddrinfo(
                    web_host, web_port, socket.AF_UNSPEC,
                    socket.SOCK_STREAM, 0, socket.AI_PASSIVE,
                )
            except socket.gaierror:
                self.log_error(
                    self._("Could not resolve backend server, ClickNLoad cannot start")
                )
                return

            for addr in addrinfo:
                test_socket = socket.socket(addr[0], socket.SOCK_STREAM)
                test_socket.settimeout(1)

                try:
                    test_socket.connect(addr[4])

                except socket.error:
                    continue

                test_socket.shutdown(socket.SHUT_WR)
                self.web_addr = addr[4]
                self.web_af = addr[0]

                self.log_debug(
                    self._("Backend found on {}://{}:{}").format(
                        "https" if self.pyload.webserver.use_ssl else "http",
                        f"[{self.web_addr[0]}]" if ":" in self.web_addr[0] else self.web_addr[0],
                        self.web_addr[1]
                    )
                )
                self.backend_found.set()
                break

            else:
                self.log_error(
                    self._("Could not connect to backend server, ClickNLoad cannot start")
                )

    @threaded
    def _activate(self):
        self.backend_found.wait(20)
        if self.backend_found.is_set():
            self.proxy()

    def activate(self):
        if not self.pyload.config.get("webui", "enabled"):
            self.log_warning(
                self._("pyLoad's Web interface is not active, ClickNLoad cannot start")
            )
            return

        self._activate()

    def deactivate(self):
        if self.server_running:
            self.log_info(self._("Shutting down proxy..."))

            self.do_exit = True

            try:
                wakeup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                wakeup_socket.connect(
                    (
                        "127.0.0.1"
                        if any(ip == self.cnl_ip for ip in ("0.0.0.0", "", "::"))
                        else self.cnl_ip,
                        self.cnl_port,
                    )
                )
                wakeup_socket.close()
            except Exception:
                pass

            self.exit_done.wait(10)
            if self.exit_done.is_set():
                self.log_debug("Server exited successfully")
            else:
                self.log_warning(
                    self._("Server was not exited gracefully, shutdown forced")
                )

    @lock
    @threaded
    def forward(self, client_socket, backend_socket, queue=False):
        if queue:
            old_ids = set(pack.pid for pack in self.pyload.api.get_collector())

        forward(client_socket, backend_socket, recv_timeout=0.5)
        forward(backend_socket, client_socket)

        if queue:
            new_ids = set(pack.pid for pack in self.pyload.api.get_collector())
            for id in new_ids - old_ids:
                self.pyload.api.push_to_queue(id)

        backend_socket.close()
        client_socket.close()

    @threaded
    def proxy(self):
        self.log_info(
            self._("Proxy listening on {}:{}").format(
                self.cnl_ip or "0.0.0.0", self.cnl_port
            )
        )
        self._server()

    @threaded
    def _server(self):
        try:
            self.exit_done.clear()

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as dock_socket:
                dock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                dock_socket.bind((self.cnl_ip, self.cnl_port))
                dock_socket.listen()

                self.server_running = True

                while True:
                    client_socket, client_addr = dock_socket.accept()

                    if not self.do_exit:
                        host, port = client_addr
                        self.log_debug(f"Connection from {host}:{port}")

                        backend_socket = socket.socket(
                            self.web_af, socket.SOCK_STREAM
                        )

                        if self.pyload.webserver.use_ssl:
                            try:
                                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                                context.check_hostname = False
                                context.verify_mode = ssl.CERT_NONE
                                backend_socket = context.wrap_socket(backend_socket, server_hostname=self.web_addr[0])

                            except Exception as exc:
                                self.log_error(self._("SSL error: {}").format(exc))
                                client_socket.close()
                                continue

                        backend_socket.connect(self.web_addr)

                        self.forward(
                            client_socket,
                            backend_socket,
                            self.config.get("dest") == "queue",
                        )

                    else:
                        break

            self.server_running = False
            self.exit_done.set()

        except socket.timeout:
            self.log_debug("Connection timed out, retrying...")
            return self._server()

        except socket.error as exc:
            self.log_error(exc)
            time.sleep(240)
            return self._server()
