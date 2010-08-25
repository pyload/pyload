#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.unescape import unescape
from module.plugins.Crypter import Crypter

class RSLayerCom(Crypter):
    __name__ = "RSLayerCom"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?rs-layer.com/directory-"
    __version__ = "0.1"
    __description__ = """RS-Layer.com Container Plugin"""
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
        link_ids = re.findall(r"onclick=\"getFile\(\'([0-9]{7}-.{8})\'\);changeBackgroundColor", self.html)
        for id in link_ids:
            new_link = unescape(re.search(r"name=\"file\" src=\"(.*)\"></frame>", self.req.load("http://rs-layer.com/link-" + id + ".html")).group(1))
            print new_link
            temp_links.append(new_link)
        self.links = temp_links
