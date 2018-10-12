# -*- coding: utf-8 -*-
import logging
import os
import threading
from builtins import _
from os.path import exists

webui = None
core = None
setup = None
log = logging.getLogger("log")


class WebServer(threading.Thread):
    def __init__(self, pycore):
        global core
        threading.Thread.__init__(self)
        self.pyload = pycore
        core = pycore
        self.running = True
        self.server = pycore.config["webui"]["server"]
        self.https = pycore.config["webui"]["https"]
        self.cert = pycore.config["ssl"]["cert"]
        self.key = pycore.config["ssl"]["key"]
        self.host = pycore.config["webui"]["host"]
        self.port = pycore.config["webui"]["port"]

        self.setDaemon(True)

    def run(self):
        from pyload import webui

        global webui

        if self.https:
            if not exists(self.cert) or not exists(self.key):
                log.warning(_("SSL certificates not found."))
                self.https = False

        if self.server in ("lighttpd", "nginx"):
            log.warning(
                _(
                    "Sorry, we dropped support for starting {} directly within pyLoad"
                ).format(self.server)
            )
            log.warning(
                _(
                    "You can use the threaded server which offers good performance and ssl,"
                )
            )
            log.warning(
                _(
                    "of course you can still use your existing {} with pyLoads fastcgi server"
                ).format(self.server)
            )
            log.warning(
                _("sample configs are located in the pyload/webui/servers directory")
            )
            self.server = "builtin"

        if self.server == "fastcgi":
            try:
                import flup
            except Exception:
                log.warning(
                    _("Can't use {}, python-flup is not installed!").format(self.server)
                )
                self.server = "builtin"
        elif self.server == "lightweight":
            try:
                import bjoern
            except Exception as e:
                log.error(_("Error importing lightweight server: {}").format(e))
                log.warning(
                    _(
                        "You need to download and compile bjoern, https://github.com/jonashaag/bjoern"
                    )
                )
                log.warning(
                    _("Copy the boern.so to pyload/lib folder or use setup.py install")
                )
                log.warning(
                    _(
                        "Of course you need to be familiar with linux and know how to compile software"
                    )
                )
                self.server = "builtin"

        if os.name == "nt":
            self.pyload.log.info(
                _(
                    "Server set to threaded, due to known performance problems on windows."
                )
            )
            self.pyload.config["webui"]["server"] = "threaded"
            self.server = "threaded"

        if self.server == "fastcgi":
            self.start_fcgi()
        elif self.server == "threaded":
            self.start_threaded()
        elif self.server == "lightweight":
            self.start_lightweight()
        else:
            self.start_builtin()

    def start_builtin(self):

        if self.https:
            log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting builtin webserver: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        webui.run_simple(host=self.host, port=self.port)

    def start_threaded(self):
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

        webui.run_threaded(
            host=self.host, port=self.port, cert=self.cert, key=self.key
        )

    def start_fcgi(self):

        self.pyload.log.info(
            _("Starting fastcgi server: {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        webui.run_fcgi(host=self.host, port=self.port)

    def start_lightweight(self):
        if self.https:
            log.warning(
                _("This server offers no SSL, please consider using threaded instead")
            )

        self.pyload.log.info(
            _("Starting lightweight webserver (bjoern): {host}:{port:d}").format(
                **{"host": self.host, "port": self.port}
            )
        )
        webui.run_lightweight(host=self.host, port=self.port)

    def quit(self):
        self.running = False
