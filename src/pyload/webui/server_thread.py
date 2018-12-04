# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import threading

from cheroot.wsgi import PathInfoDispatcher, Server

from .app import create_app


# TODO: make configurable to serve API
class WebServer(threading.Thread):
    def __init__(self, core):
        super().__init__()
        self.daemon = True

        self.pyload = core
        self._ = core._

        self.use_ssl = core.config.get("webui", "use_ssl")  #: recheck
        self.host = core.config.get("webui", "host")
        self.port = core.config.get("webui", "port")
        self.prefix = core.config.get("webui", "prefix")

        bind_addr = (self.host, self.port)
        bind_path = "{}/".format(self.prefix.strip("/"))

        self.app = create_app(core.api, core.debug)
        self.server = Server(bind_addr, PathInfoDispatcher({bind_path: self.app}))

        #: logging patches
        core.logfactory.init_logger(self.app.logger.name)
        self.server.error_log = core.logfactory.init_logger("cheroot").log

        if not self.use_ssl:
            return

        self.certfile = core.config.get("ssl", "certfile")
        self.keyfile = core.config.get("ssl", "keyfile")

        if self.certfile:
            self.server.ssl_certificate = self.certfile
        if self.keyfile:
            self.server.ssl_private_key = self.keyfile

    def run(self):
        self.pyload.log.warning(
            self._("Starting webserver: {host}:{port:d}").format(
                host=self.host, port=self.port
            )
        )
        try:
            self.server.safe_start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.pyload.log.info(self._("Stopping webserver..."))
        self.server.stop()
