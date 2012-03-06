#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time
from traceback import print_exc

from module.Api import LinkStatus
from module.common.packagetools import parseNames
from module.utils import has_method, accumulate

from BaseThread import BaseThread

class InfoThread(BaseThread):
    def __init__(self, manager, data, pid=-1, rid=-1):
        """Constructor"""
        BaseThread.__init__(self, manager)

        self.data = data
        self.pid = pid # package id
        # [ .. (name, plugin) .. ]

        self.rid = rid #result id

        self.cache = [] #accumulated data

        self.start()

    def run(self):
        """run method"""

        plugins = accumulate(self.data)
        crypter = {}

        # filter out crypter plugins
        for name in self.m.core.pluginManager.getPlugins("crypter"):
            if name in plugins:
                crypter[name] = plugins[name]
                del plugins[name]

        #directly write to database
        if self.pid > -1:
            for pluginname, urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPluginModule(pluginname)
                klass = self.m.core.pluginManager.getPluginClass(pluginname)
                if has_method(klass, "getInfo"):
                    self.fetchForPlugin(pluginname, klass, urls, self.updateDB)
                    self.m.core.files.save()
                elif has_method(plugin, "getInfo"):
                    self.log.debug("Deprecated .getInfo() method on module level, use classmethod instead")
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.m.core.files.save()

        else: #post the results
            for name, urls in crypter:
                #attach container content
                try:
                    data = self.decrypt(name, urls)
                except:
                    print_exc()
                    self.m.log.error("Could not decrypt container.")
                    data = []

                accumulate(data, plugins)

            self.m.infoResults[self.rid] = {}

            for pluginname, urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(pluginname, True)
                klass = getattr(plugin, pluginname)
                if has_method(klass, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateResult, True)
                    #force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)
                elif has_method(plugin, "getInfo"):
                    self.log.debug("Deprecated .getInfo() method on module level, use staticmethod instead")
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateResult, True)
                    #force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)
                else:
                    #generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateResult(pluginname, result, True)

            self.m.infoResults[self.rid]["ALL_INFO_FETCHED"] = {}

        self.m.timestamp = time() + 5 * 60


    def updateDB(self, plugin, result):
        self.m.core.files.updateFileInfo(result, self.pid)

    def updateResult(self, plugin, result, force=False):
        #parse package name and generate result
        #accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            #used for package generating
            tmp = [(name, (url, LinkStatus(name, plugin, "unknown", status, int(size))))
            for name, size, status, url in self.cache]

            data = parseNames(tmp)
            result = {}
            for k, v in data.iteritems():
                for url, status in v:
                    status.packagename = k
                    result[url] = status

            self.m.setInfoResults(self.rid, result)

            self.cache = []

    def updateCache(self, plugin, result):
        self.cache.extend(result)

    def fetchForPlugin(self, pluginname, plugin, urls, cb, err=None):
        try:
            result = [] #result loaded from cache
            process = [] #urls to process
            for url in urls:
                if url in self.m.infoCache:
                    result.append(self.m.infoCache[url])
                else:
                    process.append(url)

            if result:
                self.m.log.debug("Fetched %d values from cache for %s" % (len(result), pluginname))
                cb(pluginname, result)

            if process:
                self.m.log.debug("Run Info Fetching for %s" % pluginname)
                for result in plugin.getInfo(process):
                    #result = [ .. (name, size, status, url) .. ]
                    if not type(result) == list: result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res

                    cb(pluginname, result)

            self.m.log.debug("Finished Info Fetching for %s" % pluginname)
        except Exception, e:
            self.m.log.warning(_("Info Fetching for %(name)s failed | %(err)s") %
                               {"name": pluginname, "err": str(e)})
            if self.m.core.debug:
                print_exc()

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)


    def decrypt(self, plugin, urls):
        self.m.log.debug("Pre decrypting %s" % plugin)
        klass = self.m.core.pluginManager.loadClass("crypter", plugin)

        # only decrypt files
        if has_method(klass, "decryptFile"):
            urls = klass.decrypt(urls)
            data, crypter = self.m.core.pluginManager.parseUrls(urls)
            return data

        return []
