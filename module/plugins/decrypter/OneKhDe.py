#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.unescape import unescape
from module.Plugin import Plugin

class OneKhDe(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "OneKhDe"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?1kh.de/f/"
        props['version'] = "0.1"
        props['description'] = """1kh.de Container Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
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
