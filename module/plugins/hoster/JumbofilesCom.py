# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class JumbofilesCom(SimpleHoster):
    __name__    = "JumbofilesCom"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?jumbofiles\.com/(?P<ID>\w{12})'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """JumboFiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com")]


    INFO_PATTERN = r'<TR><TD>(?P<N>[^<]+?)\s*<small>\((?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Not Found or Deleted / Disabled due to inactivity or DMCA'
    LINK_FREE_PATTERN = r'<meta http-equiv="refresh" content="10;url=(.+)">'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        post_data = {'id': self.info['pattern']['ID'], 'op': "download3", 'rand': ""}
        html = self.load(self.pyfile.url, post=post_data)
        self.link = re.search(self.LINK_FREE_PATTERN, html).group(1)


getInfo = create_getInfo(JumbofilesCom)
