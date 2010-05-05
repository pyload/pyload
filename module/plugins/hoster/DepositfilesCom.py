#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class DepositfilesCom(Hoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://depositfiles.com/.{2,}/files/"
    __version__ = "0.1"
    __description__ = """Depositfiles.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def get_file_url(self):
        return urllib.unquote(re.search('<form action="(http://.+?\.depositfiles.com/.+?)" method="get"', self.html).group(1))

    def get_file_name(self):
        return re.search('File name: <b title="(.*)">', self.html).group(1)

    def file_exists(self):
        self.html = self.load(self.parent.url)
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights", self.html) != None:
            return False
        return True
