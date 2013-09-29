#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
from traceback import print_exc

from pyload.Api import LinkStatus, DownloadStatus
from pyload.utils.packagetools import parseNames
from pyload.utils import has_method, accumulate

from BaseThread import BaseThread
from DecrypterThread import DecrypterThread


class InfoThread(DecrypterThread):
    def __init__(self, manager, owner, data, pid=-1, oc=None):
        BaseThread.__init__(self, manager, owner)

        # [... (plugin, url) ...]
        self.data = data
        self.pid = pid
        self.oc = oc # online check
        # urls that already have a package name
        self.names = {}

        self.start()

    def run(self):
        plugins = accumulate(self.data)
        crypter = {}

        # filter out crypter plugins
        for name in self.m.core.pluginManager.getPlugins("crypter"):
            if name in plugins:
                crypter[name] = plugins[name]
                del plugins[name]

        if crypter:
            # decrypt them
            links, packages = self.decrypt(crypter)
            # push these as initial result and save package names
            self.updateResult(links)
            for pack in packages:
                for url in pack.getURLs():
                    self.names[url] = pack.name

                links.extend(pack.links)
                self.updateResult(pack.links)

            # TODO: no plugin information pushed to GUI
            # parse links and merge
            hoster, crypter = self.m.core.pluginManager.parseUrls([l.url for l in links])
            accumulate(hoster + crypter, plugins)

        # db or info result
        cb = self.updateDB if self.pid > 1 else self.updateResult

        for pluginname, urls in plugins.iteritems():
            plugin = self.m.core.pluginManager.getPluginModule(pluginname)
            klass = self.m.core.pluginManager.getPluginClass(pluginname)
            if has_method(klass, "getInfo"):
                self.fetchForPlugin(klass, urls, cb)
            # TODO: this branch can be removed in the future
            elif has_method(plugin, "getInfo"):
                self.log.debug("Deprecated .getInfo() method on module level, use staticmethod instead")
                self.fetchForPlugin(plugin, urls, cb)

        if self.oc:
            self.oc.done = True

        self.names.clear()
        self.m.timestamp = time() + 5 * 60

    def updateDB(self, result):
        # writes results to db
        # convert link info to tuples
        info = [(l.name, l.size, l.status, l.url) for l in result if not l.hash]
        info_hash = [(l.name, l.size, l.status, l.hash, l.url) for l in result if l.hash]
        if info:
            self.m.core.files.updateFileInfo(info, self.pid)
        if info_hash:
            self.m.core.files.updateFileInfo(info_hash, self.pid)

    def updateResult(self, result):
        tmp = {}
        parse = []
        # separate these with name and without
        for link in result:
            if link.url in self.names:
                tmp[link] = self.names[link.url]
            else:
                parse.append(link)

        data = parseNames([(link.name, link) for link in parse])
        # merge in packages that already have a name
        data = accumulate(tmp.iteritems(), data)

        self.m.setInfoResults(self.oc, data)

    def fetchForPlugin(self, plugin, urls, cb):
        """executes info fetching for given plugin and urls"""
        # also works on module names
        pluginname = plugin.__name__.split(".")[-1]
        try:
            cached = [] #results loaded from cache
            process = [] #urls to process
            for url in urls:
                if url in self.m.infoCache:
                    cached.append(self.m.infoCache[url])
                else:
                    process.append(url)

            if cached:
                self.m.log.debug("Fetched %d links from cache for %s" % (len(cached), pluginname))
                cb(cached)

            if process:
                self.m.log.debug("Run Info Fetching for %s" % pluginname)
                for result in plugin.getInfo(process):
                    #result = [ .. (name, size, status, url) .. ]
                    if not type(result) == list: result = [result]

                    links = []
                    # Convert results to link statuses
                    for res in result:
                        if isinstance(res, LinkStatus):
                            links.append(res)
                        elif type(res) == tuple and len(res) == 4:
                            links.append(LinkStatus(res[3], res[0], int(res[1]), res[2], pluginname))
                        elif type(res) == tuple and len(res) == 5:
                            links.append(LinkStatus(res[3], res[0], int(res[1]), res[2], pluginname, res[4]))
                        else:
                            self.m.log.debug("Invalid getInfo result: " + result)

                    # put them on the cache
                    for link in links:
                        self.m.infoCache[link.url] = link

                    cb(links)

            self.m.log.debug("Finished Info Fetching for %s" % pluginname)
        except Exception, e:
            self.m.log.warning(_("Info Fetching for %(name)s failed | %(err)s") %
                               {"name": pluginname, "err": str(e)})
            self.core.print_exc()