# -*- coding: utf-8 -*-


from .downloader import BaseDownloader


class DeadDownloader(BaseDownloader):
    __name__ = "DeadDownloader"
    __type__ = "downloader"
    __version__ = "0.24"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Hoster is no longer available"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    @classmethod
    def get_info(cls, *args, **kwargs):
        info = super(DeadDownloader, cls).get_info(*args, **kwargs)
        info["status"] = 1
        return info

    def setup(self):
        self.offline(self._("Hoster is no longer available"))
