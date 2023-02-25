# -*- coding: utf-8 -*-
import re

from pyload.core.network.exceptions import Fail

from ..helpers import replace_patterns
from .simple_downloader import SimpleDownloader


class MultiDownloader(SimpleDownloader):
    __name__ = "MultiDownloader"
    __type__ = "downloader"
    __version__ = "0.72"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Multi downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    OFFLINE_PATTERN = r"^unmatchable$"
    TEMP_OFFLINE_PATTERN = r"^unmatchable$"

    DIRECT_LINK = None

    def get_info(self, url="", html=""):
        return super(SimpleDownloader, self).get_info(url, html)

    def init(self):
        self.PLUGIN_NAME = self.pyload.plugin_manager.downloader_plugins.get(
            self.classname
        )["name"]

    def _log(self, level, plugintype, pluginname, args, kwargs):
        args = (self.PLUGIN_NAME,) + args
        return super()._log(level, plugintype, pluginname, args, kwargs)

    def setup(self):
        self.no_fallback = True
        self.chunk_limit = 1
        self.multi_dl = bool(self.account)
        self.resume_download = self.premium

    def _preload(self):
        pass

    def _prepare(self):
        super()._prepare()

        if self.pyfile.pluginname != self.__name__:
            overwritten_plugin = self.pyload.plugin_manager.load_class("downloader", self.pyfile.pluginname)
            if overwritten_plugin is not None:
                self.pyfile.url = replace_patterns(self.pyfile.url, overwritten_plugin.URL_REPLACEMENTS)

        if self.DIRECT_LINK is None:
            self.direct_dl = self.__pattern__ != r'^unmatchable$' and re.match(
                self.__pattern__, self.pyfile.url
            ) is not None

        else:
            self.direct_dl = self.DIRECT_LINK

    def _process(self, thread):
        try:
            super()._process(thread)

        except Fail as exc:
            hdict = self.pyload.plugin_manager.downloader_plugins.get(
                self.pyfile.pluginname, {}
            )
            if self.config.get("revert_failed", True) and hdict.get("new_module"):
                tmp_module = hdict.pop("new_module", None)
                tmp_name = hdict.pop("new_name", None)

                self.pyfile.plugin = None
                self.pyfile.init_plugin()

                hdict["new_module"] = tmp_module
                hdict["new_name"] = tmp_name

                self.restart(self._("Revert to original downloader plugin"))

            else:
                raise

    def handle_premium(self, pyfile):
        return self.handle_free(pyfile)

    def handle_free(self, pyfile):
        if self.premium:
            raise NotImplementedError

        else:
            self.fail(self._("MultiDownloader download failed"))
