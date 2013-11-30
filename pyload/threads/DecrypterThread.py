#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep

from pyload.Api import LinkStatus, DownloadStatus as DS
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

    def decrypt(self, plugin_map, password=None, err=None):
        result = []

        # TODO QUEUE_DECRYPT

        for name, urls in plugin_map.iteritems():
            klass = self.m.core.pluginManager.loadClass("crypter", name)
            plugin = None
            plugin_result = []

            #TODO: dependency check, there is a new error code for this
            if not klass:
                plugin_result.extend(LinkStatus(url, url, -1, DS.NotPossible, name) for url in urls)
                self.log.debug("Plugin for decrypting was not loaded")
            else:
                try:
                    plugin = klass(self.m.core, password)

                    try:
                        plugin_result = plugin._decrypt(urls)
                    except Retry:
                        sleep(1)
                        plugin_result = plugin._decrypt(urls)

                    plugin.logDebug("Decrypted", plugin_result)

                except Abort:
                    plugin.logInfo(_("Decrypting aborted"))
                except Exception, e:
                    plugin.logError(_("Decrypting failed"), e)

                    # generate error linkStatus
                    if err:
                        plugin_result.extend(LinkStatus(url, url, -1, DS.Failed, name) for url in urls)

                    if self.core.debug:
                        self.core.print_exc()
                        self.writeDebugReport(plugin.__name__, plugin=plugin)
                finally:
                    if plugin:
                        plugin.clean()

            result.extend(plugin_result)

        # generated packages
        packs = {}
        # urls without package
        urls = []

        # merge urls and packages
        for p in result:
            if isinstance(p, Package):
                if p.name in packs:
                    packs[p.name].urls.extend(p.urls)
                else:
                    if not p.name:
                        urls.extend(p.links)
                    else:
                        packs[p.name] = p
            else:
                urls.append(p)

        urls = uniqify(urls)

        return urls, packs.values()