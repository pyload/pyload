# -*- coding: utf-8 -*-

from .Http import Http


class BasePlugin(Http):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __version__ = "0.52"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Default hoster plugin when any other didnt fit"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

        if not self.pyfile.url.startswith("http"):
            self.fail(_("No plugin matched"))
