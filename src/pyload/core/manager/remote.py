# -*- coding: utf-8 -*-
# @author: mkaay

from __future__ import absolute_import, unicode_literals
from future import standard_library

from builtins import object, str
from traceback import print_exc

standard_library.install_aliases()


class RemoteManager(object):

    # __slots__ = ['backends', 'pyload']

    available = ["WebSocketBackend"]

    def __init__(self, core):
        self.pyload = core
        self.backends = []

    def start(self):
        host = self.pyload.config.get('rpc', 'host')
        port = self.pyload.config.get('rpc', 'port')

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
                self.pyload.log.info(
                    _("Starting {0}: {1}:{2}").format(b, host, port))
            except Exception as e:
                self.pyload.log.error(
                    _("Failed loading backend {0} | {1}").format(b, str(e)))
                if self.pyload.debug:
                    print_exc()
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
