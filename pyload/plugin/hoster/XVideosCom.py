# -*- coding: utf-8 -*-

import re
import urllib

from pyload.plugin.Hoster import Hoster


class XVideosCom(Hoster):
    __name    = "XVideos.com"
    __type    = "hoster"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?xvideos\.com/video(\d+)'

    __description = """XVideos.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = []


    def process(self, pyfile):
        site = self.load(pyfile.url)
        pyfile.name = "%s (%s).flv" % (
            re.search(r"<h2>([^<]+)<span", site).group(1),
            re.match(self.__pattern, pyfile.url).group(1),
        )
        self.download(urllib.unquote(re.search(r"flv_url=([^&]+)&", site).group(1)))
