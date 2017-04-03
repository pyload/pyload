# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from future import standard_library
standard_library.install_aliases()

from pyload.plugins import Abort, Fail, Retry
from pyload.plugins.downloader.crypter.base import Package
from pyload.utils.convert import accumulate
from pyload.utils.purge import uniqify

from ..datatype.init import (DownloadStatus, LinkStatus, ProgressInfo,
                             ProgressType)
from .plugin import PluginThread


class DecrypterThread(PluginThread):
    """
    Thread for decrypting.
    """
    __slots__ = ['_progressinfo', 'data', 'error', 'fid', 'pid']

    def __init__(self, manager, data, fid, pid, owner):
        PluginThread.__init__(self, manager, owner)
        # [...(url, plugin)...]
        self.data = data
        self.fid = fid
        self.pid = pid
        # holds the progress, while running
        self._progressinfo = None
        # holds if an error happened
        self.error = False

        self.start()

    def get_progress(self):
        return self._progressinfo

    def run(self):
        pack = self.pyload.files.get_package(self.pid)
        api = self.pyload.api.with_user_context(self.owner)
        links, packages = self.decrypt(accumulate(self.data), pack.password)

        # if there is only one package links will be added to current one
        if len(packages) == 1:
            # TODO: also rename the package (optionally)
            links.extend(packages[0].links)
            del packages[0]

        if links:
            self.pyload.log.info(
                _("Decrypted {0:d} links into package {1}").format(len(links), pack.name))
            api.add_links(self.pid, [l.url for l in links])

        for p in packages:
            api.add_package(p.name, p.get_urls(), pack.password)

        self.pyload.files.set_download_status(
            self.fid, DownloadStatus.Finished if not self.error else DownloadStatus.Failed)
        self.manager.done(self)

    def decrypt(self, plugin_map, password=None, err=False):
        result = []

        self._progressinfo = ProgressInfo("BasePlugin", "", _("decrypting"),
                                     0, 0, len(self.data), self.owner, ProgressType.Decrypting)
        # TODO: QUEUE_DECRYPT
        for name, urls in plugin_map.items():
            klass = self.pyload.pgm.load_class("crypter", name)
            plugin = None
            plugin_result = []

            # updating progress
            self._progressinfo.plugin = name
            self._progressinfo.name = _("Decrypting {0} links").format(
                len(urls) if len(urls) > 1 else urls[0])

            # TODO: dependency check, there is a new error code for this
            # TODO: decrypting with result yielding
            if not klass:
                self.error = True
                if err:
                    plugin_result.extend(LinkStatus(
                        url, url, -1, DownloadStatus.NotPossible, name) for url in urls)
                self.pyload.log.debug(
                    "Plugin '{0}' for decrypting was not loaded".format(name))
            else:
                try:
                    plugin = klass(self.pyload, password)

                    try:
                        plugin_result = plugin._decrypt(urls)
                    except Retry:
                        time.sleep(1)
                        plugin_result = plugin._decrypt(urls)

                    plugin.log_debug("Decrypted", plugin_result)

                except Abort:
                    plugin.log_info(_("Decrypting aborted"))
                except Exception as e:
                    plugin.log_error(_("Decrypting failed"), str(e))

                    self.error = True
                    # generate error linkStatus
                    if err:
                        plugin_result.extend(LinkStatus(
                            url, url, -1, DownloadStatus.Failed, name) for url in urls)

                    # no debug for intentional errors
                    if self.pyload.debug and not isinstance(e, Fail):
                        # self.pyload.print_exc()
                        # self.debug_report(plugin.__name__, plugin=plugin)
                finally:
                    if plugin:
                        plugin.clean()

            self._progressinfo.done += len(urls)
            result.extend(plugin_result)

        # clear the progress
        self._progressinfo = None

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

        return urls, list(packs.values())
