# -*- coding: utf-8 -*-


from .Http import Http


class DefaultPlugin(Http):
    __name__ = "DefaultPlugin"
    __type__ = "downloader"
    __version__ = "0.52"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Default downloader plugin when any other didnt fit"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

        if not self.pyfile.url.startswith("http"):
            self.fail(self._("No plugin matched"))
