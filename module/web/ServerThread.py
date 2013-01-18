#!/usr/bin/env python
from __future__ import with_statement
from time import time, sleep

import threading
import logging

from module.utils.fs import exists

core = None
setup = None
log = logging.getLogger("log")

class WebServer(threading.Thread):
    def __init__(self, pycore=None, pysetup=None):
        global core, setup
        threading.Thread.__init__(self)

        if pycore:
            core = pycore
            config = pycore.config
        elif pysetup:
            setup = pysetup
            config = pysetup.config
        else:
            raise Exception("No config context provided")

        self.server = config['webinterface']['server']
        self.https = config['webinterface']['https']
        self.cert = config["ssl"]["cert"]
        self.key = config["ssl"]["key"]
        self.host = config['webinterface']['host']
        self.port = config['webinterface']['port']
        self.debug = config['general']['debug_mode']
        self.force_server = config['webinterface']['force_server']
        self.error = None

        self.setDaemon(True)

    def run(self):
        self.running = True
        import webinterface
        global webinterface

        if self.https:
            if not exists(self.cert) or not exists(self.key):
                log.warning(_("SSL certificates not found."))
                self.https = False

        prefer = None

        # These cases covers all settings
        if self.server == "threaded":
            prefer = "threaded"
        elif self.server == "fastcgi":
            prefer = "flup"
        elif self.server == "fallback":
            prefer = "wsgiref"

        server = self.select_server(prefer)

        try:
            self.start_server(server)

        except Exception, e:
            log.error(_("Failed starting webserver: " + e.message))
            self.error = e
            if core:
                core.print_exc()

    def select_server(self, prefer=None):
        """ find a working server """
        from servers import all_server

        unavailable = []
        server = None
        for server in all_server:

            if self.force_server and self.force_server == server.NAME:
                break # Found server
            # When force_server is set, no further checks have to be made
            elif self.force_server:
                continue

            if prefer and prefer == server.NAME:
                break # found prefered server
            elif prefer: # prefer is similar to force, but force has precedence
                continue

            # Filter for server that offer ssl if needed
            if self.https and not server.SSL:
                continue

            try:
                if server.find():
                    break # Found a server
                else:
                    unavailable.append(server.NAME)
            except Exception, e:
                log.error(_("Failed importing webserver: " + e.message))

        if unavailable: # Just log whats not available to have some debug information
            log.debug("Unavailable webserver: " + ",".join(unavailable))

        if not server and self.force_server:
            server = self.force_server # just return the name

        return server


    def start_server(self, server):

        from servers import ServerAdapter

        if issubclass(server, ServerAdapter):

            if self.https and not server.SSL:
                log.warning(_("This server offers no SSL, please consider using threaded instead"))

            # Now instantiate the serverAdapter
            server = server(self.host, self.port, self.key, self.cert, 6, self.debug) # todo, num_connections
            name = server.NAME

        else: # server is just a string
            name = server

        log.info(_("Starting %(name)s webserver: %(host)s:%(port)d") % {"name": name, "host": self.host, "port": self.port})
        webinterface.run_server(host=self.host, port=self.port, server=server)



    # check if an error was raised for n seconds
    def check_error(self, n=1):
        t = time() + n
        while time() < t:
            if self.error:
                return self.error
            sleep(0.1)

