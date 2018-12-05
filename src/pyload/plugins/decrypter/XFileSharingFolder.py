# -*- coding: utf-8 -*-

import re
from builtins import str

from ..base.xfs_decrypter import XFSDecrypter


class XFileSharingFolder(XFSDecrypter):
    __name__ = "XFileSharingFolder"
    __type__ = "decrypter"
    __version__ = "0.25"
    __status__ = "testing"

    __pyload_version__ = "0.5"

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
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """XFileSharing dummy folder decrypter plugin for addon"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def _log(self, level, plugintype, pluginname, args, kwargs):
        args = (self.PLUGIN_NAME,) + args
        return XFSDecrypter._log(self, level, plugintype, pluginname, args, kwargs)

    def init(self):
        self.__pattern__ = self.pyload.pluginManager.crypterPlugins[self.classname][
            "pattern"
        ]

        self.PLUGIN_DOMAIN = (
            re.match(self.__pattern__, self.pyfile.url).group("DOMAIN").lower()
        )
        self.PLUGIN_NAME = "".join(
            part.capitalize()
            for part in re.split(r"\.|\d+|-", self.PLUGIN_DOMAIN)
            if part != "."
        )

    # TODO: Recheck in 0.6.x
    def setup_base(self):
        XFSDecrypter.setup_base(self)

        if self.account:
            self.req = self.pyload.requestFactory.getRequest(
                self.PLUGIN_NAME, self.account.user
            )
            # NOTE: Don't call get_info here to reduce overhead
            self.premium = self.account.info["data"]["premium"]
        else:
            self.req = self.pyload.requestFactory.getRequest(self.classname)
            self.premium = False

    # TODO: Recheck in 0.6.x
    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = str(self.PLUGIN_NAME)
        XFSDecrypter.load_account(self)
        self.__class__.__name__ = class_name
