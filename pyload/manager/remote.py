# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals

from builtins import str
from builtins import object
from traceback import print_exc


class RemoteManager(object):
    available = []

    def __init__(self, core):
        self.pyload = core
        self.backends = []

        if self.pyload.remote:
            self.available.append("WebSocketBackend")


    def start_backends(self):
        host = self.pyload.config["webui"]["wsHost"]
        port = self.pyload.config["webui"]["wsPort"]

        for b in self.available:
            klass = getattr(
                __import__("pyload.remote.%s" % b.lower(), globals(), locals(), [b.lower()], -1), b
            )
            backend = klass(self)
            if not backend.check_deps():
                continue
            try:
                backend.setup(host, port)
                self.pyload.log.info(_("Starting %(name)s: %(addr)s:%(port)s") % {"name": b, "addr": host, "port": port})
            except Exception as e:
                self.pyload.log.error(_("Failed loading backend %(name)s | %(error)s") % {"name": b, "error": str(e)})
                if self.pyload.debug:
                    print_exc()
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
