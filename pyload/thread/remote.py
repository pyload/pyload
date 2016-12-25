# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals

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
