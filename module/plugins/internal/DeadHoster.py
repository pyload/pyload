# -*- coding: utf-8 -*-

from .Hoster import Hoster


class DeadHoster(Hoster):
    __name__ = "DeadHoster"
    __type__ = "hoster"
    __version__ = "0.22"
    __status__ = "stable"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Hoster is no longer available"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    @classmethod
    def get_info(cls, *args, **kwargs):
        info = Hoster.get_info(*args, **kwargs)
        info['status'] = 1
        return info

    def setup(self):
        self.offline(_("Hoster is no longer available"))
