#!/usr/bin/env python
from __future__ import with_statement
from os.path import exists

import os
import threading
import logging

core = None
setup = None
log = logging.getLogger("log")

class WebServer(threading.Thread):
    def __init__(self, pycore):
        global core
        threading.Thread.__init__(self)
        self.core = pycore
        core = pycore
        self.running = True
        self.server = pycore.config['webinterface']['server']
        self.https = pycore.config['webinterface']['https']
        self.cert = pycore.config["ssl"]["cert"]
        self.key = pycore.config["ssl"]["key"]
        self.host = pycore.config['webinterface']['host']
        self.port = pycore.config['webinterface']['port']

        self.setDaemon(True)

    def run(self):
        import webinterface
        global webinterface

        if self.https:
            if not exists(self.cert) or not exists(self.key):
                log.warning(_("SSL certificates not found."))
                self.https = False

        if self.server == "fastcgi":
            try:
                import flup
            except:
                log.warning(_("Can't use %(server)s, python-flup is not installed!") % {
                    "server": self.server})
                self.server = "builtin"
        elif self.server == "lightweight":
            try:
                import bjoern
            except Exception, e:
                log.error(_("Error importing lightweight server: %s") % e)
                log.warning(_("You need to download and compile bjoern, https://github.com/jonashaag/bjoern"))
                log.warning(_("Copy the boern.so to module/lib folder or use setup.py install"))
                log.warning(_("Of course you need to be familiar with linux and know how to compile software"))
                self.server = "builtin"

        # threaded is the new default server
        if self.server == "builtin":
            self.server = "threaded"

        if self.server == "fastcgi":
            self.start_fcgi()
        elif self.server == "threaded":
            self.start_threaded()
        elif self.server == "lightweight":
            self.start_lightweight()
        else:
            self.start_fallback()

    def start_fallback(self):

        if self.https:
            log.warning(_("This server offers no SSL, please consider using threaded instead"))

        self.core.log.info(_("Starting builtin webserver: %(host)s:%(port)d") % {"host": self.host, "port": self.port})
        webinterface.run_simple(host=self.host, port=self.port)

    def start_threaded(self):
        if self.https:
            self.core.log.info(_("Starting threaded SSL webserver: %(host)s:%(port)d") % {"host": self.host, "port": self.port})
        else:
            self.cert = ""
            self.key = ""
            self.core.log.info(_("Starting threaded webserver: %(host)s:%(port)d") % {"host": self.host, "port": self.port})

        webinterface.run_threaded(host=self.host, port=self.port, cert=self.cert, key=self.key)

    def start_fcgi(self):

        from flup.server.threadedserver import ThreadedServer
        def noop(*args, **kwargs):
            pass

        ThreadedServer._installSignalHandlers = noop

        self.core.log.info(_("Starting fastcgi server: %(host)s:%(port)d") % {"host": self.host, "port": self.port})
        webinterface.run_fcgi(host=self.host, port=self.port)


    def start_lightweight(self):
        if self.https:
            log.warning(_("This server offers no SSL, please consider using threaded instead"))

        self.core.log.info(_("Starting lightweight webserver (bjoern): %(host)s:%(port)d") % {"host": self.host, "port": self.port})
        webinterface.run_lightweight(host=self.host, port=self.port)

    def quit(self):
        self.running = False
