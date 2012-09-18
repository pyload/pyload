#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
from traceback import print_exc

from module.utils import uniqify
from module.plugins.Base import Retry
from module.plugins.Crypter import Package

from BaseThread import BaseThread

class DecrypterThread(BaseThread):
    """thread for decrypting"""

    def __init__(self, manager, data, pid):
        """constructor"""
        BaseThread.__init__(self, manager)
        self.data = data
        self.pid = pid

        self.start()

    def run(self):
        plugin_map = {}
        for url, plugin in self.data:
            if plugin in plugin_map:
                plugin_map[plugin].append(url)
            else:
                plugin_map[plugin] = [url]

        self.decrypt(plugin_map)

    def decrypt(self, plugin_map):
        pack = self.m.core.files.getPackage(self.pid)
        result = []

        for name, urls in plugin_map.iteritems():
            klass = self.m.core.pluginManager.loadClass("crypter", name)
            plugin = klass(self.m.core, pack, pack.password)
            plugin_result = []

            try:
                try:
                    plugin_result = plugin._decrypt(urls)
                except Retry:
                    sleep(1)
                    plugin_result = plugin._decrypt(urls)
            except Exception, e:
                plugin.logError(_("Decrypting failed"), e)
                if self.m.core.debug:
                    print_exc()
                    self.writeDebugReport(plugin.__name__, plugin=plugin)

            plugin.logDebug("Decrypted", plugin_result)
            result.extend(plugin_result)

        #TODO
        result = uniqify(result)
        pack_names = {}
        urls = []

        for p in result:
            if isinstance(p, Package):
                if p.name in pack_names:
                    pack_names[p.name].urls.extend(p.urls)
                else:
                    pack_names[p.name] = p
            else:
                urls.append(p)

        if urls:
            self.log.info(_("Decrypted %(count)d links into package %(name)s") % {"count": len(urls), "name": pack.name})
            self.m.core.api.addFiles(self.pid, urls)

        for p in pack_names.itervalues():
            self.m.core.api.addPackage(p.name, p.urls, pack.password)

        if not result:
            self.log.info(_("No links decrypted"))

