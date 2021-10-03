# -*- coding: utf-8 -*-

import re

from ..internal.Hoster import Hoster


class PornhostCom(Hoster):
    __name__ = "PornhostCom"
    __type__ = "hoster"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?pornhost\.com/\d+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Pornhost.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    NAME_PATTERN = r'class="video-title">(.+?)<'
    LINK_PATTERN = r'<source src="(https://cdn\d+-dl.pornhost.com/.+)" type="video/mp4">'
    OFFLINE_PATTERN = r'>Gallery not found<'

    def process(self, pyfile):
        self.data = self.load(pyfile.url)

        if re.search(self.OFFLINE_PATTERN, self.data) is not None:
            self.offline()

        m = re.search(self.NAME_PATTERN, self.data)
        if m is None:
            self.error(_("name pattern not found"))

        pyfile.name = m.group(1) + ".mp4"

        m = re.search(self.LINK_PATTERN, self.data)
        if m is None:
            self.error(_("link pattern not found"))

        self.download(m.group(1))
