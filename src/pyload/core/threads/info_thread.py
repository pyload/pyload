# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, vuolter

from datetime import timedelta
import time

from ..api import OnlineStatus
from ..datatypes.pyfile import PyFile
from ..utils.packagetools import parseNames
from .plugin_thread import PluginThread


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
        for name in self.pyload.pluginManager.containerPlugins:
            if name in plugins:
                container.extend((name, url) for url in plugins[name])

                del plugins[name]

        # directly write to database
        if self.pid > -1:
            for pluginname, urls in plugins.items():
                plugin = self.pyload.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(pluginname, plugin, urls, self.updateDB)
                    self.pyload.files.save()

        elif self.add:
            for pluginname, urls in plugins.items():
                plugin = self.pyload.pluginManager.getPlugin(pluginname, True)
                if hasattr(plugin, "getInfo"):
                    self.fetchForPlugin(
                        pluginname, plugin, urls, self.updateCache, True
                    )

                else:
                    # generate default result
                    result = [(url, 0, 3, url) for url in urls]

                    self.updateCache(pluginname, result)

            packs = parseNames((name, url) for name, x, y, url in self.cache)

            self.pyload.log.debug(f"Fetched and generated {len(packs)} packages")

            for k, v in packs:
                self.pyload.api.addPackage(k, v)

            # empty cache
            del self.cache[:]

        else:  #: post the results

            for name, url in container:
                # attach container content
                try:
                    data = self.decryptContainer(name, url)
                except Exception:
                    self.pyload.log.warning(
                        "Could not decrypt container.",
                        exc_info=self.pyload.debug > 1,
                        stack_info=self.pyload.debug > 2,
                    )
                    data = []

                for url, plugin in data:
                    if plugin in plugins:
                        plugins[plugin].append(url)
                    else:
                        plugins[plugin] = [url]

            self.m.infoResults[self.rid] = {}

            for pluginname, urls in plugins.items():
                plugin = self.pyload.pluginManager.getPlugin(pluginname, True)
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

        self.m.timestamp = time.time() + timedelta(minutes=5).seconds

    def updateDB(self, plugin, result):
        self.pyload.files.updateFileInfo(result, self.pid)

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
                self.pyload.log.debug(
                    f"Fetched {len(result)} values from cache for {pluginname}"
                )
                cb(pluginname, result)

            if process:
                self.pyload.log.debug(f"Run Info Fetching for {pluginname}")
                for result in plugin.getInfo(process):
                    # result = [ .. (name, size, status, url) .. ]
                    if not isinstance(result, list):
                        result = [result]

                    for res in result:
                        self.m.infoCache[res[3]] = res

                    cb(pluginname, result)

            self.pyload.log.debug(f"Finished Info Fetching for {pluginname}")
        except Exception as exc:
            self.pyload.log.warning(
                self._("Info Fetching for {name} failed | {err}").format(
                    name=pluginname, err=exc
                ),
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )

            # generate default results
            if err:
                result = [(url, 0, 3, url) for url in urls]
                cb(pluginname, result)

    def decryptContainer(self, plugin, url):
        data = []
        # only works on container plugins

        self.pyload.log.debug(f"Pre-decrypting {url} with {plugin}")

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, url, url, 0, 0, "", plugin, -1, -1)

        pyfile.initPlugin()

        # little plugin lifecycle
        try:
            pyfile.plugin.setup()
            pyfile.plugin.loadToDisk()
            pyfile.plugin.decrypt(pyfile)
            pyfile.plugin.deleteTmp()

            for pack in pyfile.plugin.packages:
                pyfile.plugin.urls.extend(pack[1])

            data = self.pyload.pluginManager.parseUrls(pyfile.plugin.urls)
            self.pyload.log.debug(f"Got {len(data)} links.")

        except Exception as exc:
            self.pyload.log.debug(
                f"Pre decrypting error: {exc}",
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )
        finally:
            pyfile.release()

        return data
