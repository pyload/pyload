# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter
from module.utils import html_unescape


class OneKhDe(Crypter):
    __name__    = "OneKhDe"
    __type__    = "crypter"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?1kh\.de/f/'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """1kh.de decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org")]


    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent


    def file_exists(self):
        """
        Returns True or False
        """
        return True


    def proceed(self, url, location):
        url = self.parent.url
        self.html = self.load(url)
        link_ids = re.findall(r"<a id=\"DownloadLink_(\d*)\" href=\"http://1kh.de/", self.html)
        for id in link_ids:
            new_link = html_unescape(
                re.search("width=\"100%\" src=\"(.*)\"></iframe>", self.load("http://1kh.de/l/" + id)).group(1))
            self.urls.append(new_link)
