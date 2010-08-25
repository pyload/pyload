#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.unescape import unescape
from module.plugins.Crypter import Crypter

class OneKhDe(Crypter):
    __name__ = "OneKhDe"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?1kh.de/f/"
    __version__ = "0.1"
    __description__ = """1kh.de Container Plugin"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent
        self.html = None

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        url = self.parent.url
        self.html = self.req.load(url)
        temp_links = []
        link_ids = re.findall(r"<a id=\"DownloadLink_(\d*)\" href=\"http://1kh.de/", self.html)
        for id in link_ids:
            new_link = unescape(re.search("width=\"100%\" src=\"(.*)\"></iframe>", self.req.load("http://1kh.de/l/" + id)).group(1))
            temp_links.append(new_link)
        self.links = temp_links
