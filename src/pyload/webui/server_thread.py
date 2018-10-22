# -*- coding: utf-8 -*-
# @author: vuolter

import threading
from builtins import _

from cheroot.wsgi import PathInfoDispatcher
from cheroot.wsgi import Server as WSGIServer

from pyload.webui.app import create_app


# TODO: make configurable to serve API
class WebServer(threading.Thread):
    def __init__(self, core):
        super().__init__()
        self.daemon = True

        self.pyload = core

        self.use_ssl = core.config.get("webui", "use_ssl")  #: recheck
        self.host = core.config.get("webui", "host")
        self.port = core.config.get("webui", "port")
        self.prefix = core.config.get("webui", "prefix")

        bind_addr = (self.host, self.port)
        bind_path = "{}/".format(self.prefix.strip("/"))

        self.app = create_app(core.api, self.pyload.debug)
        self.server = WSGIServer(bind_addr, PathInfoDispatcher({bind_path: self.app}))

        if not self.use_ssl:
            return

        self.certfile = core.config.get("ssl", "certfile")
        self.keyfile = core.config.get("ssl", "keyfile")

        if self.certfile:
            server.ssl_certificate = self.certfile
        if self.keyfile:
            server.ssl_private_key = self.keyfile

    def run(self):
        self.pyload.log.warning(
            self._("Starting Webserver: {host}:{port:d}").format(
                host=self.host, port=self.port
            )
        )
        try:
            self.server.safe_start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.pyload.log.info(self._("Stopping Webserver"))
        self.server.stop()
