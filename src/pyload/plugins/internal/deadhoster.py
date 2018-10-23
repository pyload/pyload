# -*- coding: utf-8 -*-
from builtins import _

from pyload.plugins.internal.hoster import Hoster


class DeadHoster(Hoster):
    __name__ = "DeadHoster"
    __type__ = "hoster"
    __version__ = "0.24"
    __status__ = "stable"

    __pyload_version__ = "0.5"

    __pattern__ = r"^unmatchable$"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Hoster is no longer available"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    @classmethod
    def get_info(cls, *args, **kwargs):
        info = super(DeadHoster, cls).get_info(*args, **kwargs)
        info["status"] = 1
        return info

    def setup(self):
        self.offline(self._("Hoster is no longer available"))
