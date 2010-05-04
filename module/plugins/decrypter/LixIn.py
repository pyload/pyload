#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Plugin import Plugin

class LixIn(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "LixIn"
        props['type'] = "container"
        props['pattern'] = r"http://(www.)?lix.in/"
        props['version'] = "0.1"
        props['description'] = """Lix.in Container Plugin"""
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
        new_link = ""
        if not re.search("captcha_img.php", self.html):
            new_link = re.search(r".*<iframe  name=\"ifram\" src=\"(.*)\" marginwidth=\"0\".*", self.req.load(url, post={"submit" : "continue"})).group(1)

        self.links = [new_link]
