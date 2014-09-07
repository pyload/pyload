# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class JumbofilesCom(SimpleHoster):
    __name__ = "JumbofilesCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?jumbofiles.com/(\w{12}).*'

    __description__ = """JumboFiles.com hoster plugin"""
    __author_name__ = "godofdream"
    __author_mail__ = "soilfiction@gmail.com"

    FILE_INFO_PATTERN = r'<TR><TD>(?P<N>[^<]+?)\s*<small>\((?P<S>[\d.]+)\s*(?P<U>[KMG][bB])\)</small></TD></TR>'
    OFFLINE_PATTERN = r'Not Found or Deleted / Disabled due to inactivity or DMCA'
    LINK_PATTERN = r'<meta http-equiv="refresh" content="10;url=(.+)">'


    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):
        ukey = re.match(self.__pattern__, self.pyfile.url).group(1)
        post_data = {"id": ukey, "op": "download3", "rand": ""}
        html = self.load(self.pyfile.url, post=post_data, decode=True)
        url = re.search(self.LINK_PATTERN, html).group(1)
        self.logDebug("Download " + url)
        self.download(url)


getInfo = create_getInfo(JumbofilesCom)
