#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from Plugin import Plugin

class FourChan(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "FourChan"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?(img\.)?(zip\.)?4chan.org/\w+/(res/|imgboard\.html)"
        props['version'] = "0.1"
        props['description'] = """4chan.org Thread Download Plugin"""
        props['author_name'] = ("Spoob")
        props['author_mail'] = ("Spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        url = self.parent.url
        html = self.req.load(url)
        link_pattern = ""
        temp_links = []
        if "imagebord.html" in url:
            link_pattern = '[<a href="(res/\d*\.html)">Reply</a>]'
            temp_links = re.findall(link_pattern, html)
            for link in re.findall(link_pattern, html):
                temp_links.append(link)
        else:
            temp_links = re.findall('File : <a href="(http://(?:img\.)?(?:zip\.)?4chan\.org/\w{,3}/src/\d*\..{3})"', html)
        self.links = temp_links
