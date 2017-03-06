# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, unicode_literals,
                        with_statement)

import logging
import os
import time

from future import standard_library

from pyload.utils.layer.safethreading import Event, Thread

standard_library.install_aliases()


core = None
setup = None
log = logging.getLogger('pyload')


class WebServer(Thread):

    __slots__ = [
        'cert',
        'debug',
        'error',
        'force_server',
        'host',
        'https',
        'key',
        'port',
        'server']

    def __init__(self, pycore=None, pysetup=None):
        global core, setup
        Thread.__init__(self)

        if pycore:
            core = pycore
            config = pycore.config
        elif pysetup:
            setup = pysetup
            config = pysetup.config
        else:
            raise Exception("No config context provided")

        self.server = config.get('webui', 'server')
        self.https = config.get('aal', 'activated')
        self.cert = config.get('ssl', 'cert')
        self.key = config.get('ssl', 'key')
        self.host = config.get('webui', 'host')
        self.port = config.get('webui', 'port')
        self.debug = config.get('webui', 'debug')
        self.force_server = config.get('webui', 'force_server')
        self.error = None

        self.setDaemon(True)

    def run(self):
        self.running = Event()
        self.running.set()

        global webinterface
        from pyload.webui import interface as webinterface

        if self.https:
            if not os.path.exists(self.cert) or not os.path.exists(self.key):
                log.warning(_("SSL certificates not found"))
                self.https = False

        if webinterface.UNAVAILALBE:
            log.warning(_("WebUI built is not available"))
        # elif webinterface.APP_PATH == "app":
            # log.info(_("Running webui in development mode"))

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

        except Exception as e:
            log.error(_("Failed starting webserver: {}").format(e.message))
            self.error = e
            # if core:
            # core.print_exc()

    def select_server(self, prefer=None):
        """
        Find a working server.
        """
        from pyload.webui.servers import all_server

        unavailable = []
        server = None
        for server in all_server:

            if self.force_server and self.force_server == server.NAME:
                break  #: Found server
            # When force_server is set, no further checks have to be made
            elif self.force_server:
                continue

            if prefer and prefer == server.NAME:
                break  #: found prefered server
            elif prefer:  #: prefer is similar to force, but force has precedence
                continue

            # Filter for server that offer ssl if needed
            if self.https and not server.SSL:
                continue

            try:
                if server.find():
                    break  #: Found a server
                else:
                    unavailable.append(server.NAME)
            except Exception as e:
                log.error(
                    _("Failed importing webserver: {}").format(
                        e.message))

        if unavailable:  #: Just log whats not available to have some debug information
            log.debug("Unavailable webserver: {}".format(
                ", ".join(unavailable)))

        if not server and self.force_server:
            server = self.force_server  #: just return the name

        return server

    def start_server(self, server):

        from pyload.webui.servers import ServerAdapter

        if issubclass(server, ServerAdapter):

            if self.https and not server.SSL:
                log.warning(
                    _("This server offers no SSL, please consider using threaded instead"))
            elif not self.https:
                self.cert = self.key = None  #: This implicitly disables SSL
                # there is no extra argument for the server adapter
                # TODO: check for openSSL ?

            # Now instantiate the serverAdapter
            server = server(self.host, self.port, self.key,
                            self.cert, 6, self.debug)  #: todo, num_connections
            name = server.NAME

        else:  #: server is just a string
            name = server

        log.info(_("Starting {} webserver: {}:{:d}").format(
            name, self.host, self.port))
        webinterface.run_server(host=self.host, port=self.port, server=server)

    # check if an error was raised for n seconds
    def check_error(self, n=1):
        t = time.time() + n
        while time.time() < t:
            if self.error:
                return self.error
            time.sleep(0.1)
