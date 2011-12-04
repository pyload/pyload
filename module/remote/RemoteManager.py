# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay
"""

from threading import Thread
from traceback import print_exc

class BackendBase(Thread):
    def __init__(self, manager):
        Thread.__init__(self)
        self.m = manager
        self.core = manager.core
        self.enabled = True
        self.running = False

    def run(self):
        self.running = True
        try:
            self.serve()
        except Exception, e:
            self.core.log.error(_("Remote backend error: %s") % e)
            if self.core.debug:
                print_exc()
        finally:
            self.running = False

    def setup(self, host, port):
        pass

    def checkDeps(self):
        return True

    def serve(self):
        pass

    def shutdown(self):
        pass

    def stop(self):
        self.enabled = False# set flag and call shutdowm message, so thread can react
        self.shutdown()


class RemoteManager():
    available = []

    def __init__(self, core):
        self.core = core
        self.backends = []

        if self.core.remote:
            self.available.append("ThriftBackend")
#        else:
#            self.available.append("SocketBackend")


    def startBackends(self):
        host = self.core.config["remote"]["listenaddr"]
        port = self.core.config["remote"]["port"]

        for b in self.available:
            klass = getattr(__import__("module.remote.%s" % b, globals(), locals(), [b], -1), b)
            backend = klass(self)
            if not backend.checkDeps():
                continue
            try:
                backend.setup(host, port)
                self.core.log.info(_("Starting %(name)s: %(addr)s:%(port)s") % {"name": b, "addr": host, "port": port})
            except Exception, e:
                self.core.log.error(_("Failed loading backend %(name)s | %(error)s") % {"name": b, "error": str(e)})
                if self.core.debug:
                    print_exc()
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
