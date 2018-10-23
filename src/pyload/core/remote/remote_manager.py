# -*- coding: utf-8 -*-
# @author: mkaay

from builtins import _, object, str
from threading import Thread


class BackendBase(Thread):
    def __init__(self, manager):
        super().__init__()
        self.m = manager
        self.pyload = manager.pyload
        self._ = manager.pyload._
        self.enabled = True

    def run(self):
        try:
            self.serve()
        except Exception as e:
            self.pyload.log.error(self._("Remote backend error: {}").format(e))

    def setup(self, host, port):
        pass

    def checkDeps(self):
        return True

    def serve(self):
        pass

    def shutdown(self):
        pass

    def stop(self):
        self.enabled = False  #: set flag and call shutdowm message, so thread can react
        self.shutdown()


class RemoteManager(object):
    available = []

    def __init__(self, core):
        self.pyload = core
        self._ = core._
        self.backends = []

        if self.pyload.remote:
            self.available.append("ThriftBackend")

    #        else:
    #            self.available.append("SocketBackend")

    def startBackends(self):
        host = self.pyload.config.get("remote", "host")
        port = self.pyload.config.get("remote", "port")

        for b in self.available:
            klass = getattr(
                __import__(
                    "pyload.core.remote.{}".format(b.lower()), globals(), locals(), [b], 0
                ),
                b,
            )
            backend = klass(self)
            if not backend.checkDeps():
                continue
            try:
                backend.setup(host, port)
                self.pyload.log.warning(
                    self._("Starting {name}: {addr}:{port}").format(
                        name=b, addr=host, port=port
                    )
                )
            except Exception as e:
                self.pyload.log.error(
                    self._("Failed loading backend {name} | {error}").format(
                        name=b, error=str(e)
                    )
                )
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
