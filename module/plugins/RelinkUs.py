#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.Plugin import Plugin

class RelinkUs(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RelinkUs"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?relink.us/go.php"
        props['version'] = "0.1"
        props['description'] = """Relink.us Container Plugin"""
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
        container_id = url.split("id=")[-1]
        temp_links = []
        link_number = len(re.findall(r"test_\d+", self.html))
        for number in range(0, link_number):
            new_link = re.search("src='(.*)'></iframe>", self.req.load("http://relink.us/f/%s/1/%i" % (container_id, number))).group(1)
            temp_links.append(new_link)
            print temp_links
        self.links = temp_links
