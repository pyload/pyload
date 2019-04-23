# -*- coding: utf-8 -*-

import re
from module.network.HTTPRequest import BadHeader

from .Http import Http

class LibGenComics(Http):
    __name__ = "LibGenComics"
    __type__ = "hoster"
    __version__ = "0.10"
    __status__ = "testing"

    __pattern__ = r'https?://libgen.io/comics0/.+\.(cbr|cbz|zip|rar|pdf)'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Download comics from libgen.io respecting throttling limits"""
    __license__ = "GPLv3"
    __authors__ = [("Yann Jouanique", "yann.jouanique@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True
        self.multiDL = False
        self.multi_dl = False
        self.limitDL = 1
        self.limit_dl = 1

    def process(self, pyfile):
        url = re.sub(r'^(jd|py)', "http", pyfile.url)

        for _i in range(2):
            try:
                self.download(url, ref=False, disposition=True, fixurl=False)
            except BadHeader, e:
                if e.code not in (401, 403, 404, 410):
                    raise

            if self.req.code in (404, 410):
                self.offline()
            else:
                break

        self.check_download()

