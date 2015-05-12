# -*- coding: utf-8 -*-
# @author: RaNaN

import os
import sys
import time
import traceback

from Queue import Queue
from copy import copy
from pprint import pformat
from types import MethodType

from pyload.Api import OnlineStatus
from pyload.Datatype import PyFile
from pyload.Thread.Plugin import PluginThread


class InfoThread(PluginThread):

    def __init__(self, manager, data, pid=-1, rid=-1, add=False):
        """Constructor"""
        PluginThread.__init__(self, manager)

        self.data = data
        self.pid = pid  #: package id
        # [ .. (name, plugin) .. ]

        self.rid = rid  #: result id
        self.add = add  #: add packages instead of return result

        self.cache = []  #: accumulated data

        self.start()


    def run(self):
        """run method"""

        plugins = {}
        container = []

        for url, plugintype, pluginname in self.data:
            # filter out container plugins
            if plugintype == 'container':
                container.appen((pluginname, url))
            else:
                if (plugintype, pluginname) in plugins:
                    plugins[(plugintype, pluginname)].append(url)
                else:
                    plugins[(plugintype, pluginname)] = [url]

        # directly write to database
        if self.pid > -1:
            for (plugintype, pluginname), urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(plugintype, pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.m.core.files.save()

        elif self.add:
            for (plugintype, pluginname), urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(plugintype, pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateCache, True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateCache(pluginname, result)

            packs = parseNames([(name, url) for name, x, y, url in self.cache])

            self.m.log.debug("Fetched and generated %d packages" % len(packs))

            for k, v in packs:
                self.m.core.api.addPackage(k, v)

            # empty cache
            del self.cache[:]

        else:  #: post the results

            for name, url in container:
                # attach container content
                try:
                    data = self.decryptContainer(name, url)
                except Exception:
                    traceback.print_exc()
                    self.m.log.error("Could not decrypt container.")
                    data = []

                for url, plugintype, pluginname in data:
                    try:
                        plugins[plugintype][pluginname].append(url)
                    except Exception:
                        plugins[plugintype][pluginname] = [url]

            self.m.infoResults[self.rid] = {}

            for plugintype, pluginname, urls in plugins.iteritems():
                plugin = self.m.core.pluginManager.getPlugin(plugintype, pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateResult, True)

                    # force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateResult(pluginname, result, True)

            self.m.infoResults[self.rid]['ALL_INFO_FETCHED'] = {}

        self.m.timestamp = time.time() + 5 * 60


    def updateDB(self, plugin, result):
        self.m.core.files.updateFileInfo(result, self.pid)


    def updateResult(self, plugin, result, force=False):
        # parse package name and generate result
        # accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            # used for package generating
            tmp = [(name, (url, OnlineStatus(name, plugin, "unknown", status, int(size)))) for name, size, status, url in self.cache]

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
            result = []  #: result loaded from cache
            process = []  #: urls to process
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
                    # result = [ .. (name, size, status, url) .. ]
                    if not type(result) == list:
                        result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res  # : why don't assign res dict directly?

                    cb(pluginname, result)

            self.m.log.debug("Finished Info Fetching for %s" % pluginname)
        except Exception, e:
            self.m.log.warning(_("Info Fetching for %(name)s failed | %(err)s") % {"name": pluginname, "err": str(e)})
            if self.m.core.debug:
                traceback.print_exc()

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)


    def decryptContainer(self, plugin, url):
        data = []
        # only works on container plugins

        self.m.log.debug("Pre decrypting %s with %s" % (url, plugin))

        # dummy pyfile
        pyfile = PyFile(self.m.core.files, -1, url, url, 0, 0, "", plugin, -1, -1)

        pyfile.initPlugin()

        # little plugin lifecycle
        try:
            pyfile.plugin.setup()
            pyfile.plugin.loadToDisk()
            pyfile.plugin.decrypt(pyfile)
            pyfile.plugin.deleteTmp()

            for pack in pyfile.plugin.packages:
                pyfile.plugin.urls.extend(pack[1])

            data = self.m.core.pluginManager.parseUrls(pyfile.plugin.urls)

            self.m.log.debug("Got %d links." % len(data))

        except Exception, e:
            self.m.log.debug("Pre decrypting error: %s" % str(e))
        finally:
            pyfile.release()

        return data
