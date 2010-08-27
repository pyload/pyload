#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Hoster import Hoster

class ShragleCom(Hoster):
    __name__ = "ShragleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?shragle.com/files/"
    __version__ = "0.1"
    __description__ = """Shragle Download PLugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        if self.html is None:
            self.download_html()
        self.parent.status.filename = self.get_file_name()
        self.parent.status.url = self.get_file_url()
        self.parent.status.wait = self.wait_until()

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url)
        self.time_plus_wait = time.time() + 10

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        self.fileID = re.search(r"name=\"fileID\" value=\"([^\"]+)", self.html).group(1)
        self.dlSession = re.search(r"name=\"dlSession\" value=\"([^\"]+)", self.html).group(1)
        self.userID = ""
        self.password = ""
        self.lang = "de"
        return "http://srv4.shragle.com/download.php"

    def get_file_name(self):
        if self.html is None:
            self.download_html()

        file_name_pattern = r"<\/div><h2>(.+)<\/h2"
        return re.search(file_name_pattern, self.html).group(1)

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()

        if re.search(r"html", self.html) is None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.download(url, location, {'fileID': self.fileID, 'dlSession': self.dlSession, 'userID': self.userID, 'password': self.password, 'lang': self.lang})
