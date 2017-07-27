# -*- coding: utf-8 -*-
# @author: mkaay

from __future__ import absolute_import, unicode_literals

from builtins import str
from traceback import print_exc

from future import standard_library

from pyload.core.manager.base import BaseManager

standard_library.install_aliases()


class RemoteManager(BaseManager):

    available = ["WebSocketBackend"]

    def __init__(self, core):
        BaseManager.__init__(self, core)
        self.backends = []

    def start(self):
        host = self.pyload_core.config.get('rpc', 'host')
        port = self.pyload_core.config.get('rpc', 'port')

        for b in self.available:
            klass = getattr(
                __import__("pyload.rpc.{0}".format(b.lower()),
                           globals(), locals(), [b.lower()], -1), b
            )
            backend = klass(self)
            if not backend.check_deps():
                continue
            try:
                backend.setup(host, port)
                self.pyload_core.log.info(
                    self._("Starting {0}: {1}:{2}").format(b, host, port))
            except Exception as e:
                self.pyload_core.log.error(
                    self._("Failed loading backend {0} | {1}").format(
                        b, str(e)))
                if self.pyload_core.debug:
                    print_exc()
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
