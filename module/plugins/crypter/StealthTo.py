#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class StealthTo(Crypter):
    __name__ = "StealthTo"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?stealth.to/folder/"
    __version__ = "0.1"
    __description__ = """Stealth.to Container Plugin"""
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
        self.html = self.req.load(url, cookies=True)
        temp_links = []
        ids = []
        ats = [] # authenticity_token
        inputs = re.findall(r"(<(input|form)[^>]+)", self.html)
        for input in inputs:
            if re.search(r"name=\"authenticity_token\"",input[0]):
                ats.append(re.search(r"value=\"([^\"]+)", input[0]).group(1))
            if re.search(r"name=\"id\"",input[0]):
                ids.append(re.search(r"value=\"([^\"]+)", input[0]).group(1))
                
        for i in range(0, len(ids)):
            self.req.load(url + "/web", post={"authenticity_token": ats[i], "id": str(ids[i]), "link": ("download_" + str(ids[i]))}, cookies=True)
            new_html = self.req.load(url + "/web", post={"authenticity_token": ats[i], "id": str(ids[i]), "link": "1"}, cookies=True)
            temp_links.append(re.search(r"iframe src=\"(.*)\" frameborder", new_html).group(1))

        self.links = temp_links
