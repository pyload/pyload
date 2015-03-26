# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class JumbofilesCom(SimpleHoster):
    __name    = "JumbofilesCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?jumbofiles\.com/(?P<ID>\w{12})'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """JumboFiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]


    INFO_PATTERN = r'<TR><TD>(?P<N>[^<]+?)\s*<small>\((?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Not Found or Deleted / Disabled due to inactivity or DMCA'
    LINK_FREE_PATTERN = r'<meta http-equiv="refresh" content="10;url=(.+)">'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        post_data = {"id": self.info['pattern']['ID'], "op": "download3", "rand": ""}
        html = self.load(self.pyfile.url, post=post_data, decode=True)
        self.link = re.search(self.LINK_FREE_PATTERN, html).group(1)
