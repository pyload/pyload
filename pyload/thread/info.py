# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from time import time

from pyload.api import LinkStatus, DownloadStatus, ProgressInfo, ProgressType
from pyload.utils.packagetools import parse_names
from pyload.utils import has_method, accumulate

from pyload.thread.base import BaseThread
from pyload.thread.decrypter import DecrypterThread


class InfoThread(DecrypterThread):
    def __init__(self, manager, owner, data, pid=-1, oc=None):
        BaseThread.__init__(self, manager, owner)

        # [...(url, plugin)...]
        self.data = data
        self.pid = pid
        self.oc = oc # online check
        # urls that already have a package name
        self.names = {}

        self.progress = None

        self.manager.add_thread(self)
        self.start()

    def run(self):
        plugins = accumulate(self.data)
        crypter = {}

        # db or info result
        cb = self.update_db if self.pid > 1 else self.update_result

        # filter out crypter plugins
        for name in self.manager.pyload.pluginmanager.get_plugins("crypter"):
            if name in plugins:
                crypter[name] = plugins[name]
                del plugins[name]

        if crypter:
            # decrypt them
            links, packages = self.decrypt(crypter, err=True)
            # push these as initial result and save package names
            cb(links)
            for pack in packages:
                for url in pack.get_urls():
                    self.names[url] = pack.name

                links.extend(pack.links)
                cb(pack.links)

            # TODO: no plugin information pushed to GUI
            # parse links and merge
            hoster, crypter = self.manager.pyload.pluginmanager.parse_urls(l.url for l in links)
            accumulate(hoster + crypter, plugins)

        self.progress = ProgressInfo("BasePlugin", "", _("online check"), 0, 0, sum(len(urls) for urls in plugins.values()),
                                     self.owner, ProgressType.LinkCheck)

        for pluginname, urls in plugins.items():
            plugin = self.manager.pyload.pluginmanager.load_module("hoster", pluginname)
            klass = self.manager.pyload.pluginmanager.get_plugin_class("hoster", pluginname, overwrite=False)
            if has_method(klass, "get_info"):
                self.fetch_for_plugin(klass, urls, cb)
            # TODO: this branch can be removed in the future
            elif has_method(plugin, "get_info"):
                self.log.debug("Deprecated .get_info() method on module level, use staticmethod instead")
                self.fetch_for_plugin(plugin, urls, cb)

        if self.oc:
            self.oc.done = True

        self.names.clear()
        self.manager.timestamp = time() + 5 * 60
        self.progress = None
        self.finished()

    def update_db(self, result):
        # writes results to db
        # convert link info to tuples
        info = [(l.name, l.size, l.status, l.url) for l in result if not l.hash]
        info_hash = [(l.name, l.size, l.status, l.hash, l.url) for l in result if l.hash]
        if info:
            self.manager.pyload.files.update_file_info(info, self.pid)
        if info_hash:
            self.manager.pyload.files.update_file_info(info_hash, self.pid)

    def update_result(self, result):
        tmp = {}
        parse = []
        # separate these with name and without
        for link in result:
            if link.url in self.names:
                tmp[link] = self.names[link.url]
            else:
                parse.append(link)

        data = parse_names((link.name, link) for link in parse)
        # merge in packages that already have a name
        data = accumulate(tmp.items(), data)

        # TODO: self.oc is None ?!
        self.manager.set_info_results(self.oc, data)

    def fetch_for_plugin(self, plugin, urls, cb):
        """executes info fetching for given plugin and urls"""
        # also works on module names
        pluginname = plugin.__name__.split(".")[-1]

        self.progress.plugin = pluginname
        self.progress.name = _("Checking {:d} links").format(len(urls))

        # final number of links to be checked
        done = self.progress.done + len(urls)
        try:
            cached = [] #results loaded from cache
            process = [] #urls to process
            for url in urls:
                if url in self.manager.info_cache:
                    cached.append(self.manager.info_cache[url])
                else:
                    process.append(url)

            if cached:
                self.manager.log.debug("Fetched {:d} links from cache for {}".format(len(cached), pluginname))
                self.progress.done += len(cached)
                cb(cached)

            if process:
                self.manager.log.debug("Run Info Fetching for {}".format(pluginname))
                for result in plugin.get_info(process):
                    #result = [ .. (name, size, status, url) .. ]
                    if not isinstance(result, list): result = [result]

                    links = []
                    # Convert results to link statuses
                    for res in result:
                        if isinstance(res, LinkStatus):
                            links.append(res)
                        elif isinstance(res, tuple) and len(res) == 4:
                            links.append(LinkStatus(res[3], res[0], int(res[1]), res[2], pluginname))
                        elif isinstance(res, tuple) and len(res) == 5:
                            links.append(LinkStatus(res[3], res[0], int(res[1]), res[2], pluginname, res[4]))
                        else:
                            self.manager.log.debug("Invalid get_info result: {}".format(result))

                    # put them on the cache
                    for link in links:
                        self.manager.info_cache[link.url] = link

                    self.progress.done += len(links)
                    cb(links)

            self.manager.log.debug("Finished Info Fetching for {}".format(pluginname))
        except Exception as e:
            self.manager.log.warning(_("Info Fetching for {} failed | {}").format(pluginname, e.message))
            self.pyload.print_exc()
        finally:
            self.progress.done = done
