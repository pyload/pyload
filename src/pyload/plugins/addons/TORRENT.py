# -*- coding: utf-8 -*-
import re

from ..base.addon import BaseAddon


class TORRENT(BaseAddon):
    __name__ = "TORRENT"
    __type__ = "addon"
    __version__ = "0.07"
    __status__ = "testing"

    __config__ = [("enabled", "bool", "Activated", True),
                  ("torrent_plugin",
                   "None;c:AlldebridComTorrent;c:DebridlinkFrTorrent;h:LinksnappyComTorrent;c:RealdebridComTorrent;h:ZbigzCom",
                   "Associate torrents / magnets with plugin", "None")]

    __description__ = """Associate torrents / magnets with plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001@yahoo.com")]

    def activate(self):
        self.pyload.addon_manager.add_event("plugin_updated", self.plugins_updated)
        self.torrent_plugin = self.config.get("torrent_plugin")
        self._associate(self.torrent_plugin)
        self._report_status()

    def deactivate(self):
        self.pyload.addon_manager.remove_event("plugin_updated", self.plugins_updated)
        self._remove_association(self.torrent_plugin)
        self.torrent_plugin = "None"
        if self.pyload.exiting is False:
            self._report_status()

    def plugins_updated(self, updated_plugins):
        if self.torrent_plugin != "None":
            self._remove_association(self.torrent_plugin)
            self._associate(self.torrent_plugin)

    def config_changed(self, *args):
        if args[3] == "plugin" and args[0] == "TORRENT" and args[1] == "torrent_plugin" and args[2] != self.torrent_plugin:
            self._remove_association(self.torrent_plugin)
            self.torrent_plugin = args[2]
            self._associate(self.torrent_plugin)
            self._report_status()

    def _report_status(self):
        if self.torrent_plugin == "None":
            self.log_warning(self._("torrents / magnets are not associated with any plugin"))
        else:
            self.log_info(self._("Using {} to handle torrents / magnets").format(self.torrent_plugin.split(":")[1]))

    def _associate(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(":")
            plugin_type = "decrypter" if plugin_type == "c" else "downloader"

            hdict = self.pyload.plugin_manager.plugins["container"]["TORRENT"]
            hdict["pattern"] = r"(?!(?:file|https?)://).+\.(?:torrent|magnet)"
            hdict["re"] = re.compile(hdict["pattern"])

            hdict = self.pyload.plugin_manager.plugins[plugin_type][plugin_name]
            hdict["pattern"] = r"(?:file|https?)://.+\.torrent|magnet:\?.+"
            hdict["re"] = re.compile(hdict["pattern"])

    def _remove_association(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(":")
            plugin_type = "decrypter" if plugin_type == "c" else "downloader"

            hdict = self.pyload.plugin_manager.plugins[plugin_type][plugin_name]
            hdict["pattern"] = r"^unmatchable$"
            hdict["re"] = re.compile(hdict["pattern"])

            hdict = self.pyload.plugin_manager.plugins["container"]["TORRENT"]
            hdict["pattern"] = r"(?:file|https?)://.+\.torrent|magnet:\?.+|(?!(?:file|https?)://).+\.(?:torrent|magnet)"
            hdict["re"] = re.compile(hdict["pattern"])

