# -*- coding: utf-8 -*-

import re

from ..internal.misc import uniqify
from ..internal.Addon import Addon


class TORRENT(Addon):
    __name__ = "TORRENT"
    __type__ = "hook"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("torrent_plugin", "None;h:ZbigzCom", "Associate torrents / magnets with plugin", "None")]

    __description__ = """Associate torrents / magnets with plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001@yahoo.com")]

    _PAT_TORRENT = r'(?:file|https?)://.+\.torrent|magnet:\?.+'
    _RE_TORRENT = re.compile(_PAT_TORRENT)
    _PAT_UNMATCHABLE = r'^unmatchable$'
    _RE_UNMATCHABLE = re.compile(_PAT_UNMATCHABLE)

    _RE_TORRENT_PLUGIN = re.compile(r'.+Torrent$')

    def activate(self):
        self.torrent_plugin = self.config.get("torrent_plugin")

        plugins_list = self.pyload.config.plugin['TORRENT']['torrent_plugin']['type'].split(';')
        plugins_list = self._get_torrent_plugins(plugins_list)
        self.pyload.config.plugin['TORRENT']['torrent_plugin']['type'] = ";".join(plugins_list)
        self.config.set("torrent_plugin", self.torrent_plugin)  #: Save config

        self._associate(self.torrent_plugin)
        self._report_status()

    def deactivate(self):
        self._remove_association(self.torrent_plugin)
        self._report_status()

    def config_changed(self, *args):
        if args[3] == "plugin" and args[0] == "TORRENT" and args[1] == "torrent_plugin" and args[2] != self.torrent_plugin:
            self._remove_association(self.torrent_plugin)
            self.torrent_plugin = args[2]
            self._associate(self.torrent_plugin)
            self._report_status()

    def _report_status(self):
        if self.torrent_plugin == "None":
            self.log_warning(_("torrents / magnets are not associated with any plugin"))
        else:
            self.log_info(_("Using %s to handle torrents / magnets") % self.torrent_plugin.split(":")[1])

    def _get_torrent_plugins(self, default_plugins):
        plugins = []
        plugins.extend(default_plugins)

        for t in (("crypter", "c"), ("hoster", "h")):
            for p in self.pyload.pluginManager.plugins[t[0]].values():
                if self._RE_TORRENT_PLUGIN.search(p['name'], re.I):
                    plugins.append("%s:%s" % (t[1], p['name']))

        plugins = uniqify(plugins)

        return plugins

    def _associate(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(':')
            plugin_type = "crypter" if plugin_type == "c" else "hoster"

            dict = self.pyload.pluginManager.plugins['crypter']['TORRENT']
            dict['pattern'] = self._PAT_UNMATCHABLE
            dict['re'] = self._RE_UNMATCHABLE

            dict = self.pyload.pluginManager.plugins[plugin_type][plugin_name]
            dict['pattern'] = self._PAT_TORRENT
            dict['re'] = self._RE_TORRENT

    def _remove_association(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(':')
            plugin_type = "crypter" if plugin_type == "c" else "hoster"

            dict = self.pyload.pluginManager.plugins[plugin_type][plugin_name]
            dict['pattern'] = self._PAT_UNMATCHABLE
            dict['re'] = self._RE_UNMATCHABLE

            dict = self.pyload.pluginManager.plugins['crypter']['TORRENT']
            dict['pattern'] = self._PAT_TORRENT
            dict['re'] = self._RE_TORRENT

