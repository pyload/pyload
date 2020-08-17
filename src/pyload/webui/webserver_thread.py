# -*- coding: utf-8 -*-

import logging
import threading

from cheroot import wsgi
from cheroot.ssl.builtin import BuiltinSSLAdapter

from .app import App


# TODO: make configurable to serve API
class WebServerThread(threading.Thread):
    def __init__(self, pycore):
        super().__init__()
        self.daemon = True

        self.pyload = pycore
        self._ = pycore._

        self.develop = self.pyload.config.get("webui", "develop")

        self.use_ssl = self.pyload.config.get("webui", "use_ssl")  #: recheck
        self.certfile = self.pyload.config.get("webui", "ssl_certfile")
        self.keyfile = self.pyload.config.get("webui", "ssl_keyfile")
        self.certchain = self.pyload.config.get("webui", "ssl_certchain") or None

        self.host = self.pyload.config.get("webui", "host")
        self.port = self.pyload.config.get("webui", "port")
        self.prefix = self.pyload.config.get("webui", "prefix")

        # NOTE: Is really the right choice pass the pycore obj directly to app?!
        #       Or should we pass just core.api and server.logger instead?
        self.app = App(self.pyload, self.develop)
        self.log = self.app.logger

    def _run_develop(self):
        # TODO: inject our custom logger in werkzeug code?
        # NOTE: use_reloader=True -> 'ValueError: signal only works in main thread'
        self.app.run(self.host, self.port, use_reloader=False)

    def _run_produc(self):
        bind_path = self.prefix.strip("/") + "/"
        bind_addr = (self.host, self.port)
        wsgi_app = wsgi.PathInfoDispatcher({bind_path: self.app})

        server = wsgi.Server(bind_addr, wsgi_app)

        if self.use_ssl:
            server.ssl_adapter = BuiltinSSLAdapter(
                self.certfile, self.keyfile, self.certchain
            )

        #: hack cheroot to use our custom logger
        server.error_log = lambda *args, **kwgs: self.log.log(
            kwgs.get("level", logging.ERROR), args[0], exc_info=self.pyload.debug
        )

        server.safe_start()

    def run(self):
        self.log.warning(
            self._("Starting webserver: {host}:{port}").format(
                host=self.host, port=self.port
            )
        )
        if self.develop:
            self._run_develop()
        else:
            self._run_produc()
