#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BaseThread import BaseThread

class DecrypterThread(BaseThread):
    """thread for decrypting"""

    def __init__(self, manager, data, package):
        """constructor"""
        BaseThread.__init__(self, manager)
        self.queue = data
        self.package = package

        self.m.log.debug("Starting Decrypt thread")

        self.start()

    def add(self, data):
        self.queue.extend(data)

    def run(self):
        plugin_map = {}
        for plugin, url in self.queue:
            if plugin in plugin_map:
                plugin_map[plugin].append(url)
            else:
                plugin_map[plugin] = [url]


        self.decrypt(plugin_map)

    def decrypt(self, plugin_map):
        for name, urls in plugin_map.iteritems():
            p = self.m.core.pluginManager.loadClass("crypter", name)
