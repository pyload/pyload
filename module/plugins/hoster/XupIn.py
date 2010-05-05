#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class XupIn(Hoster):
    __name__ = "XupIn"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?xup.in/"
    __version__ = "0.1"
    __description__ = """Xup.in Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False
        self.posts = {}
        self.url = self.parent.url
        if "xup.in/pic" in self.parent.url:
            self.url = self.parent.url.replace("xup.in/pic", "xup.in/dl")

    def get_file_url(self):
        self.posts["vid"] = re.search('"hidden" value="(.*)" name="vid"', self.html).group(1)
        self.posts["vtime"] = re.search('"hidden" value="(.*)" name="vtime"', self.html).group(1)
        file_url_pattern = r"<form action=\"(.*)\" method=\"post\">"
        return re.search(file_url_pattern, self.html).group(1)

    def get_file_name(self):
        file_name_pattern = r"<legend> <b>(.+?)</b> </legend>"
        return re.search(file_name_pattern, self.html).group(1)

    def file_exists(self):
        self.html = self.load(self.url)
        if re.search(r"File does not exist", self.html) != None or self.html == "":
            return False
        return True

    def proceed(self, url, location):
        self.download(url, location, post=self.posts)
