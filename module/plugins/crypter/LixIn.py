#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class LixIn(Crypter):
    __name__ = "LixIn"
    __type__ = "container"
    __pattern__ = r"http://(www.)?lix.in/"
    __version__ = "0.1"
    __description__ = """Lix.in Container Plugin"""
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
        new_link = ""
        if not re.search("captcha_img.php", self.html):
            new_link = re.search(r".*<iframe  name=\"ifram\" src=\"(.*)\" marginwidth=\"0\".*", self.req.load(url, post={"submit" : "continue"})).group(1)

        self.links = [new_link]
