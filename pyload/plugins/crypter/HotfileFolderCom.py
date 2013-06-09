#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class HotfileFolderCom(Crypter):
    __name__ = "HotfileFolderCom"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?hotfile.com/list/\w+/\w+"
    __version__ = "0.2"
    __description__ = """HotfileFolder Download Plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def decryptURL(self, url):
        html = self.load(url)

        new_links = []
        for link in re.findall(r'href="(http://(www.)?hotfile\.com/dl/\d+/[0-9a-zA-Z]+[^"]+)', html):
            new_links.append(link[0])

        if new_links:
            self.logDebug("Found %d new links" % len(new_links))
            return new_links
        else:
            self.fail('Could not extract any links')

