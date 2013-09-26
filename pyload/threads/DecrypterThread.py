#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep

from pyload.utils import uniqify, accumulate
from pyload.plugins.Base import Abort, Retry
from pyload.plugins.Crypter import Package

from BaseThread import BaseThread

class DecrypterThread(BaseThread):
    """thread for decrypting"""

    def __init__(self, manager, data, pid):
        # TODO: owner
        BaseThread.__init__(self, manager)
        # [... (plugin, url) ...]
        self.data = data
        self.pid = pid

        self.start()

    def run(self):
        pack = self.m.core.files.getPackage(self.pid)
        links, packages = self.decrypt(accumulate(self.data), pack.password)

        if links:
            self.log.info(_("Decrypted %(count)d links into package %(name)s") % {"count": len(links), "name": pack.name})
            self.m.core.api.addFiles(self.pid, [l.url for l in links])

        # TODO: add single package into this one and rename it?
        # TODO: nested packages
        for p in packages:
            self.m.core.api.addPackage(p.name, p.getURLs(), pack.password)

    def decrypt(self, plugin_map, password=None):
        result = []

        # TODO QUEUE_DECRYPT

        for name, urls in plugin_map.iteritems():
            klass = self.m.core.pluginManager.loadClass("crypter", name)
            plugin = klass(self.m.core, password)
            plugin_result = []

            try:
                try:
                    plugin_result = plugin._decrypt(urls)
                except Retry:
                    sleep(1)
                    plugin_result = plugin._decrypt(urls)
            except Abort:
                plugin.logInfo(_("Decrypting aborted"))
            except Exception, e:
                plugin.logError(_("Decrypting failed"), e)
                if self.core.debug:
                    self.core.print_exc()
                    self.writeDebugReport(plugin.__name__, plugin=plugin)
            finally:
                plugin.clean()

            plugin.logDebug("Decrypted", plugin_result)
            result.extend(plugin_result)

        # generated packages
        pack_names = {}
        # urls without package
        urls = []

        # merge urls and packages
        for p in result:
            if isinstance(p, Package):
                if p.name in pack_names:
                    pack_names[p.name].urls.extend(p.urls)
                else:
                    if not p.name:
                        urls.append(p)
                    else:
                        pack_names[p.name] = p
            else:
                urls.append(p)

        urls = uniqify(urls)

        return urls, pack_names.values()