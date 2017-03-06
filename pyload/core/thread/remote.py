# -*- coding: utf-8 -*-
# @author: mkaay

from __future__ import absolute_import, division, unicode_literals

from traceback import print_exc

from future import standard_library

from pyload.utils.layer.safethreading import Event, Thread

standard_library.install_aliases()


class RemoteBackend(Thread):

    __slots__ = ['enabled', 'manager', 'pyload', 'running']

    def __init__(self, manager):
        Thread.__init__(self)
        self.manager = manager
        self.pyload = manager.pyload
        self.enabled = True
        self.running = Event()

    def run(self):
        self.running.set()
        try:
            self.serve()
        except Exception as e:
            self.pyload.log.error(
                _("Remote backend error: {0}").format(e.message))
            if self.pyload.debug:
                print_exc()
        finally:
            self.running.clear()

    def setup(self, host, port):
        raise NotImplementedError

    def check_deps(self):
        return True

    def serve(self):
        raise NotImplementedError

    def shutdown(self):
        raise NotImplementedError

    def stop(self):
        self.enabled = False  #: set flag and call shutdowm message, so thread can react
        self.shutdown()
