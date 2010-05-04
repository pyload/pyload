#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.unescape import unescape
from module.plugins.Plugin import Plugin

class RSLayerCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RSLayerCom"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?rs-layer.com/directory-"
        props['version'] = "0.1"
        props['description'] = """RS-Layer.com Container Plugin"""
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
        link_ids = re.findall(r"onclick=\"getFile\(\'([0-9]{7}-.{8})\'\);changeBackgroundColor", self.html)
        for id in link_ids:
            new_link = unescape(re.search(r"name=\"file\" src=\"(.*)\"></frame>", self.req.load("http://rs-layer.com/link-" + id + ".html")).group(1))
            print new_link
            temp_links.append(new_link)
        self.links = temp_links
