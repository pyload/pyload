# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

import os
import pprint
import time
import traceback
from builtins import _, str
from copy import copy
from queue import Queue
from sys import exc_info
from threading import Thread
from types import MethodType

import pycurl
from pyload.api import OnlineStatus
from pyload.datatype.pyfile import PyFile
from pyload.plugins.plugin import Abort, Fail, Reconnect, Retry, SkipDownload
from pyload.utils.packagetools import parseNames
from pyload.thread.plugin_thread import PluginThread


class InfoThread(PluginThread):
    def __init__(self, manager, data, pid=-1, rid=-1, add=False):
        """
        Constructor.
        """
        super().__init__(manager)

        self.data = data
        self.pid = pid  #: package id
        # [ .. (name, plugin) .. ]

        self.rid = rid  #: result id
        self.add = add  #: add packages instead of return result

        self.cache = []  #: accumulated data

        self.start()

    def run(self):
        """
        run method.
        """

        plugins = {}
        container = []

        for url, plugin in self.data:
            if plugin in plugins:
                plugins[plugin].append(url)
            else:
                plugins[plugin] = [url]

        # filter out container plugins
        for name in self.m.pyload.pluginManager.containerPlugins:
            if name in plugins:
                container.extend((name, url) for url in plugins[name])

                del plugins[name]

        # directly write to database
        if self.pid > -1:
            for pluginname, urls in plugins.items():
                plugin = self.m.pyload.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.m.pyload.files.save()

        elif self.add:
            for pluginname, urls in plugins.items():
                plugin = self.m.pyload.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(
                        pluginname, plugin, urls, self.updateCache, True
                    )

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateCache(pluginname, result)

            packs = parseNames((name, url) for name, x, y, url in self.cache)

            self.m.log.debug("Fetched and generated {} packages".format(len(packs)))

            for k, v in packs:
                self.m.pyload.api.addPackage(k, v)

            # empty cache
            del self.cache[:]

        else:  #: post the results

            for name, url in container:
                # attach container content
                try:
                    data = self.decryptContainer(name, url)
                except Exception:
                    self.m.log.error("Could not decrypt container.")
                    data = []

                for url, plugin in data:
                    if plugin in plugins:
                        plugins[plugin].append(url)
                    else:
                        plugins[plugin] = [url]

            self.m.infoResults[self.rid] = {}

            for pluginname, urls in plugins.items():
                plugin = self.m.pyload.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(
                        pluginname, plugin, urls, self.updateResult, True
                    )

                    # force to process cache
                    if self.cache:
                        self.updateResult(pluginname, [], True)

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateResult(pluginname, result, True)

            self.m.infoResults[self.rid]["ALL_INFO_FETCHED"] = {}

        self.m.timestamp = time.time() + 5 * 60

    def updateDB(self, plugin, result):
        self.m.pyload.files.updateFileInfo(result, self.pid)

    def updateResult(self, plugin, result, force=False):
        # parse package name and generate result
        # accumulate results

        self.cache.extend(result)

        if len(self.cache) >= 20 or force:
            # used for package generating
            tmp = [
                (name, (url, OnlineStatus(name, plugin, "unknown", status, int(size))))
                for name, size, status, url in self.cache
            ]

            data = parseNames(tmp)
            result = {}
            for k, v in data.items():
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
                self.m.log.debug(
                    "Fetched {} values from cache for {}".format(
                        len(result), pluginname
                    )
                )
                cb(pluginname, result)

            if process:
                self.m.log.debug("Run Info Fetching for {}".format(pluginname))
                for result in plugin.getInfo(process):
                    # result = [ .. (name, size, status, url) .. ]
                    if not isinstance(result, list):
                        result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res

                    cb(pluginname, result)

            self.m.log.debug("Finished Info Fetching for {}".format(pluginname))
        except Exception as e:
            self.m.log.warning(
                _("Info Fetching for {name} failed | {err}").format(
                    name=pluginname, err=str(e)
                )
            )

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)

    def decryptContainer(self, plugin, url):
        data = []
        # only works on container plugins

        self.m.log.debug("Pre decrypting {} with {}".format(url, plugin))

        # dummy pyfile
        pyfile = PyFile(self.m.pyload.files, -1, url, url, 0, 0, "", plugin, -1, -1)

        pyfile.initPlugin()

        # little plugin lifecycle
        try:
            pyfile.plugin.setup()
            pyfile.plugin.loadToDisk()
            pyfile.plugin.decrypt(pyfile)
            pyfile.plugin.deleteTmp()

            for pack in pyfile.plugin.packages:
                pyfile.plugin.urls.extend(pack[1])

            data = self.m.pyload.pluginManager.parseUrls(pyfile.plugin.urls)

            self.m.log.debug("Got {} links.".format(len(data)))

        except Exception as e:
            self.m.log.debug("Pre decrypting error: {}".format(str(e)))
        finally:
            pyfile.release()

        return data
