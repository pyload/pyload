# -*- coding: utf-8 -*-

from .simple_decrypter import SimpleDecrypter


class MultiDecrypter(SimpleDecrypter):
    __name__ = "MultiDecrypter"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Multi decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def init(self):
        self.PLUGIN_NAME = self.pyload.plugin_manager.decrypter_plugins.get(
            self.classname
        )["name"]

    def _log(self, level, plugintype, pluginname, args, kwargs):
        args = (self.PLUGIN_NAME,) + args
        return super()._log(level, plugintype, pluginname, args, kwargs)
