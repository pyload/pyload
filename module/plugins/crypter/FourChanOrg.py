#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class FourChanOrg(Crypter):
    __name__ = "FourChanOrg"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?(img\.)?(zip\.)?4chan.org/\w+/(res/|imgboard\.html)"
    __version__ = "0.1"
    __description__ = """4chan.org Thread Download Plugin"""
    __author_name__ = ("Spoob")
    __author_mail__ = ("Spoob@pyload.org")

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
