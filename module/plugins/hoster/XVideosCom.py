# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.Hoster import Hoster


class XVideosCom(Hoster):
    __name__ = "XVideos.com"
    __version__ = "0.1"
    __pattern__ = r'http://(?:www\.)?xvideos\.com/video([0-9]+)/.*'
    __description__ = """XVideos.com hoster plugin"""
    __author_name__ = ""
    __author_mail__ = ""

    def process(self, pyfile):
        site = self.load(pyfile.url)
        pyfile.name = "%s (%s).flv" % (
            re.search(r"<h2>([^<]+)<span", site).group(1),
            re.match(self.__pattern__, pyfile.url).group(1),
        )
        self.download(urllib.unquote(re.search(r"flv_url=([^&]+)&", site).group(1)))
