# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import logging
import threading

from cheroot.wsgi import PathInfoDispatcher, Server

from .app import App


# TODO: make configurable to serve API
class WebServer(threading.Thread):
    def __init__(self, pycore):
        super().__init__()
        self.daemon = True

        self.pyload = pycore
        self._ = pycore._

        self.develop = self.pyload.config.get("webui", "develop")
        self.use_ssl = self.pyload.config.get("webui", "use_ssl")  #: recheck
        self.host = self.pyload.config.get("webui", "host")
        self.port = self.pyload.config.get("webui", "port")
        self.prefix = self.pyload.config.get("webui", "prefix")

        bind_addr = (self.host, self.port)
        bind_path = "{}/".format(self.prefix.strip("/"))

        self.app = App(self.pyload, self.develop)
        self.server = Server(bind_addr, PathInfoDispatcher({bind_path: self.app}))

        self.log = self.app.logger
        self.server.error_log = lambda *args, **kwgs: self.log.log(kwgs.get("level", logging.ERROR), args[0], exc_info=self.develop, stack_info=self.develop)  #: use our custom logger in cheroot with few hacks

        if not self.use_ssl:
            return

        self.certfile = self.pyload.config.get("ssl", "certfile")
        self.keyfile = self.pyload.config.get("ssl", "keyfile")

        if self.certfile:
            self.server.ssl_certificate = self.certfile
        if self.keyfile:
            self.server.ssl_private_key = self.keyfile

    def run(self):
        self.log.warning(
            self._("Starting webserver: {host}:{port:d}").format(
                host=self.host, port=self.port
            )
        )
        try:
            self.server.safe_start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.log.info(self._("Stopping webserver..."))
        self.server.stop()
