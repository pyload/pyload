# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class JumbofilesCom(SimpleHoster):
    __name    = "JumbofilesCom"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?jumbofiles\.com/(\w{12}).*'

    __description = """JumboFiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]


    INFO_PATTERN = r'<TR><TD>(?P<N>[^<]+?)\s*<small>\((?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Not Found or Deleted / Disabled due to inactivity or DMCA'
    LINK_PATTERN = r'<meta http-equiv="refresh" content="10;url=(.+)">'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self):
        ukey = re.match(self.__pattern, self.pyfile.url).group(1)
        post_data = {"id": ukey, "op": "download3", "rand": ""}
        html = self.load(self.pyfile.url, post=post_data, decode=True)
        url = re.search(self.LINK_PATTERN, html).group(1)
        self.download(url)


getInfo = create_getInfo(JumbofilesCom)
