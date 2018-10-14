# -*- coding: utf-8 -*-

import os
import re
import urllib.parse
from builtins import _, str

from pyload.plugins.internal.hoster import Hoster
from pyload.plugins.utils import json


class RedtubeCom(Hoster):
    __name__ = "RedtubeCom"
    __type__ = "hoster"
    __version__ = "0.27"
    __pyload_version__ = "0.5"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?redtube\.com/\d+"
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Redtube.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de")]

    NAME_PATTERN = r'videoTitle: "(?P<N>.+?)",'

    def process(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(r"sources: ({.+?}),", html)
        if m is None:
            self.error(_("sources pattern not found"))

        sources = json.loads(m.group(1))
        quality = str(max(int(q) for q in sources.keys()))

        link = sources[quality]

        m = re.search(self.NAME_PATTERN, html)
        if m is None:
            self.error(_("name pattern not found"))

        ext = os.path.splitext(urllib.parse.urlparse(link).path)[1]
        pyfile.name = m.group(1) + ext

        self.download(link)
