import re

from ..base.addon import BaseAddon


class NZB(BaseAddon):
    __name__ = "NZB"
    __type__ = "addon"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [("enabled", "bool", "Activated", True),
                  ("nzb_plugin",
                   "None;c:TorboxAppNzb;",
                   "Associate nzb with plugin", "None")]

    __description__ = """Associate nzb with plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001@yahoo.com")]

    def activate(self):
        self.pyload.addon_manager.add_event("plugin_updated", self.plugins_updated)
        self.nzb_plugin = self.config.get("nzb_plugin")
        self._associate(self.nzb_plugin)
        self._report_status()

    def deactivate(self):
        self.pyload.addon_manager.remove_event("plugin_updated", self.plugins_updated)
        self._remove_association(self.nzb_plugin)
        self.nzb_plugin = "None"
        if self.pyload.exiting is False:
            self._report_status()

    def plugins_updated(self, updated_plugins):
        if self.nzb_plugin != "None":
            self._remove_association(self.nzb_plugin)
            self._associate(self.nzb_plugin)

    def config_changed(self, *args):
        if args[3] == "plugin" and args[0] == "NZB" and args[1] == "nzb_plugin" and args[2] != self.nzb_plugin:
            self._remove_association(self.nzb_plugin)
            self.nzb_plugin = args[2]
            self._associate(self.nzb_plugin)
            self._report_status()

    def _report_status(self):
        if self.nzb_plugin == "None":
            self.log_warning(self._("nzb is not associated with any plugin"))
        else:
            self.log_info(self._("Using {} to handle nzb").format(self.nzb_plugin.split(":")[1]))

    def _associate(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(":")
            plugin_type = "decrypter" if plugin_type == "c" else "downloader"

            hdict = self.pyload.plugin_manager.plugins["container"]["NZB"]
            hdict["pattern"] = r"(?!(?:file|https?)://).+\.nzb"
            hdict["re"] = re.compile(hdict["pattern"])

            hdict = self.pyload.plugin_manager.plugins[plugin_type][plugin_name]
            hdict["pattern"] = r"(?:file|https?)://.+\.nzb"
            hdict["re"] = re.compile(hdict["pattern"])

    def _remove_association(self, plugin):
        if plugin != "None":
            plugin_type, plugin_name = plugin.split(":")
            plugin_type = "decrypter" if plugin_type == "c" else "downloader"

            hdict = self.pyload.plugin_manager.plugins[plugin_type][plugin_name]
            hdict["pattern"] = r"^unmatchable$"
            hdict["re"] = re.compile(hdict["pattern"])

            hdict = self.pyload.plugin_manager.plugins["container"]["NZB"]
            hdict["pattern"] = r"(?:file|https?)://.+\.nzb|(?!(?:file|https?)://).+\.nzb"
            hdict["re"] = re.compile(hdict["pattern"])

