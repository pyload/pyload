# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time
from builtins import int, str

from future import standard_library

from pyload.utils import parse
from pyload.utils.check import hasmethod
from pyload.utils.misc import accumulate

from ..datatype.init import LinkStatus, ProgressInfo, ProgressType
from .decrypter import DecrypterThread
from .plugin import PluginThread

standard_library.install_aliases()


class InfoThread(DecrypterThread):

    __slots__ = ['_progress', 'data', 'oc', 'pid']

    def __init__(self, manager, owner, data, pid=-1, oc=None):
        PluginThread.__init__(self, manager, owner)

        # [...(url, plugin)...]
        self.data = data
        self.pid = pid
        self.oc = oc  # online check
        # urls that already have a package name
        self.names = {}

        self.__pi = None  # ProgressInfo

    def start(self):
        self.__manager.add_thread(self)
        DecrypterThread.start(self)

    def run(self):
        plugins = accumulate(self.data)
        crypter = {}

        # db or info result
        cb = self.update_db if self.pid > 1 else self.update_result

        # filter out crypter plugins
        for name in self.pyload_core.pgm.get_plugins("crypter"):
            if name in plugins:
                crypter[name] = plugins[name]
                del plugins[name]

        if crypter:
            # decrypt them
            links, packages = self.decrypt(crypter)
            # push these as initial result and save package names
            cb(links)
            for pack in packages:
                for url in pack.get_urls():
                    self.names[url] = pack.name

                links.extend(pack.links)
                cb(pack.links)

            # TODO: no plugin information pushed to GUI
            # parse links and merge
            hoster, crypter = self.pyload_core.pgm.parse_urls(
                l.url for l in links)
            accumulate(hoster + crypter, plugins)

        self.__pi = ProgressInfo(
            "BasePlugin", "", self._("online check"), 0, 0,
            sum(len(urls) for urls in plugins.values()), self.owner,
            ProgressType.LinkCheck
        )
        for pluginname, urls in plugins.items():
            plugin = self.pyload_core.pgm.load_module("hoster", pluginname)
            klass = self.pyload_core.pgm.get_plugin_class(
                "hoster", pluginname, overwrite=False)
            if hasmethod(klass, "get_info"):
                self.fetch_for_plugin(klass, urls, cb)
            # TODO: this branch can be removed in the future
            elif hasmethod(plugin, "get_info"):
                self.pyload_core.log.debug(
                    "Deprecated .get_info() method on module level, "
                    "use staticmethod instead")
                self.fetch_for_plugin(plugin, urls, cb)

        if self.oc:
            self.oc.done = True

        self.names.clear()
        self.__manager.timestamp = time.time() + 5 * 60
        self.__pi = None
        self.finished()

    def update_db(self, result):
        # writes results to db
        # convert link info to tuples
        info = [(l.name, l.size, l.status, l.url)
                for l in result if not l.hash]
        info_hash = [(l.name, l.size, l.status, l.hash, l.url)
                     for l in result if l.hash]
        if info:
            self.pyload_core.files.update_file_info(info, self.pid)
        if info_hash:
            self.pyload_core.files.update_file_info(info_hash, self.pid)

    def update_result(self, result):
        tmp = {}
        res = []
        # separate these with name and without
        for link in result:
            if link.url in self.names:
                tmp[link] = self.names[link.url]
            else:
                res.append(link)

        data = parse.packs((link.name, link) for link in res)
        # merge in packages that already have a name
        data = accumulate(tmp.items(), data)

        # TODO: self.oc is None ?!
        self.__manager.set_info_results(self.oc, data)

    def fetch_for_plugin(self, plugin, urls, cb):
        """
        Executes info fetching for given plugin and urls.
        """
        # also works on module names
        pluginname = plugin.__name__.split(".")[-1]

        self.__pi.plugin = pluginname
        self.__pi.name = self._("Checking {0:d} links").format(len(urls))

        # final number of links to be checked
        done = self.__pi.done + len(urls)
        try:
            cached = []  # results loaded from cache
            process = []  # urls to process
            for url in urls:
                if url in self.__manager.info_cache:
                    cached.append(self.__manager.info_cache[url])
                else:
                    process.append(url)

            if cached:
                self.__manager.log.debug(
                    "Fetched {0:d} links from cache for {1}".format(
                        len(cached),
                        pluginname))
                self.__pi.done += len(cached)
                cb(cached)

            if process:
                self.__manager.log.debug(
                    "Run Info Fetching for {0}".format(pluginname))
                for result in plugin.get_info(process):
                    # result = [ .. (name, size, status, url) .. ]
                    if not isinstance(result, list):
                        result = [result]

                    links = []
                    # Convert results to link statuses
                    for res in result:
                        if isinstance(res, LinkStatus):
                            links.append(res)
                        elif isinstance(res, tuple) and len(res) == 4:
                            links.append(
                                LinkStatus(
                                    res[3],
                                    res[0],
                                    int(res[1]),
                                    res[2],
                                    pluginname))
                        elif isinstance(res, tuple) and len(res) == 5:
                            links.append(LinkStatus(res[3], res[0], int(
                                res[1]), res[2], pluginname, res[4]))
                        else:
                            self.__manager.log.debug(
                                "Invalid get_info result: {0}".format(result))

                    # put them on the cache
                    for link in links:
                        self.__manager.info_cache[link.url] = link

                    self.__pi.done += len(links)
                    cb(links)

            self.__manager.log.debug(
                "Finished Info Fetching for {0}".format(pluginname))
        except Exception as e:
            self.__manager.log.warning(
                self._("Info Fetching for {0} failed | {1}").format(
                    pluginname, str(e)))
            # self.pyload_core.print_exc()
        finally:
            self.__pi.done = done
