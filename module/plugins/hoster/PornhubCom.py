# -*- coding: utf-8 -*-

import os
import re
import urlparse

from ..internal.Hoster import Hoster


class PornhubCom(Hoster):
    __name__ = "PornhubCom"
    __type__ = "hoster"
    __version__ = "0.57"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?pornhub\.com/view_video\.php\?viewkey=\w+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Pornhub.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de")]

    NAME_PATTERN = r'"video_title":"(.+?)"'

    def process(self, pyfile):
        html = self.load(pyfile.url)

        m = re.findall(r'var player_quality_(\d+)\w+? = \'(.+?)\'', html)
        if m is None:
            self.error(_("video quality pattern not found"))

        urls = dict(m)

        quality = str(max(int(q) for q in urls.keys()))

        m = re.search(self.NAME_PATTERN, html)
        if m is None:
            self.error("name pattern not found")

        link = urls[quality]

        ext = os.path.splitext(urlparse.urlparse(link).path)[1]
        pyfile.name = m.group(1) + ext

        self.download(link)
