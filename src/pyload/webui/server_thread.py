# -*- coding: utf-8 -*-

import os
import threading
from builtins import _

PYLOAD_API = None


class WebServer(threading.Thread):
    def __init__(self, core):
        global PYLOAD_API

        threading.Thread.__init__(self)

        self.pyload = core
        PYLOAD_API = core.api

        self.app = None
        self.running = True

        self.server = core.config.get("webui", "server").lower()
        self.https = core.config.get("webui", "https")
        self.cert = core.config.get("ssl", "cert")
        self.key = core.config.get("ssl", "key")
        self.host = core.config.get("webui", "host")
        self.port = core.config.get("webui", "port")

        self.setDaemon(True)

    def run(self):
        from pyload.webui import app

        self.app = app

        if self.https:
            if not os.path.exists(self.cert) or not os.path.exists(self.key):
                self.pyload.log.warning(_("SSL certificates not found."))
                self.https = False

        if self.server == "fastcgi":
            try:
                import flup
            except Exception:
                self.pyload.log.warning(
                    _("Can't use {}, python-flup is not installed!").format(self.server)
                )
                self.server = "builtin"
                
        elif self.server == "bjoern":
            try:
                import bjoern
            except Exception as e:
                self.pyload.log.error(
                    _("Error importing lightweight server: {}").format(e)
                )
                self.pyload.log.warning(
                    _(
                        "You need to download and compile bjoern, https://github.com/jonashaag/bjoern"
                    )
                )
                self.pyload.log.warning(
                    _("Copy the boern.so to pyload/lib folder or use setup.py install")
                )
                self.pyload.log.warning(
                    _(
                        "Of course you need to be familiar with linux and know how to compile software"
                    )
                )
                self.server = "builtin"

        # if self.server == "auto":
            # self.start_auto()
        # elif self.server == "cherrypy":
            # self.start_cherrypy()
        # elif self.server == "bjoern":
            # self.start_bjoern()
        # elif self.server == "fastcgi":
            # self.start_fcgi()
        # else:
            # self.start_wgsi()
        self.start_flask()

        
    def start_flask(self):
        if self.https:
            self.pyload.log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting flask webserver: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        self.app.run_flask(host=self.host, port=self.port, debug=self.pyload.debug)
        
        
    def start_wgsi(self):
        if self.https:
            self.pyload.log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting builtin webserver: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        self.app.run_wgsi(host=self.host, port=self.port, debug=self.pyload.debug)

        
    def start_auto(self):
        if self.https:
            self.pyload.log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting auto webserver: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        self.app.run_auto(host=self.host, port=self.port, debug=self.pyload.debug)
        
        
    def start_cherrypy(self):
        if self.https:
            self.pyload.log.info(
                _("Starting threaded SSL webserver: {host}:{port:d}").format(
                    **{"host": self.host, "port": self.port}
                )
            )
        else:
            self.cert = ""
            self.key = ""
            self.pyload.log.info(
                _("Starting threaded webserver: {host}:{port:d}").format(
                    **{"host": self.host, "port": self.port}
                )
            )

        self.app.run_cherrypy(
            host=self.host, port=self.port, debug=self.pyload.debug, cert=self.cert, key=self.key
        )

    def start_fcgi(self):

        self.pyload.log.info(
            _("Starting fastcgi server: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        self.app.run_fcgi(host=self.host, port=self.port, debug=self.pyload.debug)

    def start_bjoern(self):
        if self.https:
            self.pyload.log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting lightweight webserver (bjoern): {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        self.app.run_bjoern(host=self.host, port=self.port, debug=self.pyload.debug)

    def quit(self):
        self.running = False
