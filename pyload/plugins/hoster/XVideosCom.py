# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.Hoster import Hoster


class XVideosCom(Hoster):
    __name__ = "XVideos.com"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?xvideos\.com/video([0-9]+)/.*'

    __description__ = """XVideos.com hoster plugin"""
    __author_name__ = None
    __author_mail__ = None


    def process(self, pyfile):
        site = self.load(pyfile.url)
        pyfile.name = "%s (%s).flv" % (
            re.search(r"<h2>([^<]+)<span", site).group(1),
            re.match(self.__pattern__, pyfile.url).group(1),
        )
        self.download(unquote(re.search(r"flv_url=([^&]+)&", site).group(1)))
