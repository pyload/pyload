# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals

from builtins import str
from builtins import object
from threading import Thread
from traceback import print_exc


class BackendBase(Thread):
    def __init__(self, manager):
        Thread.__init__(self)
        self.manager = manager
        self.pyload = manager.pyload
        self.enabled = True
        self.running = False

    def run(self):
        self.running = True
        try:
            self.serve()
        except Exception as e:
            self.pyload.log.error(_("Remote backend error: %s") % e)
            if self.pyload.debug:
                print_exc()
        finally:
            self.running = False

    def setup(self, host, port):
        pass

    def check_deps(self):
        return True

    def serve(self):
        pass

    def shutdown(self):
        pass

    def stop(self):
        self.enabled = False# set flag and call shutdowm message, so thread can react
        self.shutdown()


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
            if not backend.checkDeps():
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
