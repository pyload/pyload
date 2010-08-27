#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class YoupornCom(Hoster):
    __name__ = "YoupornCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?youporn\.com/watch/.+"
    __version__ = "0.1"
    __description__ = """Youporn.com Video Download Hoster"""
    __author_name__ = ("willnix")
    __author_mail__ = ("willnix@pyload.org")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds

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
        self.html = self.load(url, post={"user_choice":"Enter"}, cookies=False)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        file_url = re.search(r'(http://download.youporn.com/download/\d*/.*\?download=1&ll=1&t=dd)">', self.html).group(1)
        return file_url

    def get_file_name(self):
        if self.html is None:
            self.download_html()

        file_name_pattern = r".*<title>(.*) - Free Porn Videos - YouPorn.com Lite \(BETA\)</title>.*"
        return re.search(file_name_pattern, self.html).group(1).replace("&amp;", "&").replace("/","") + '.flv'

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        if re.search(r"(.*invalid video_id.*)", self.html) is not None:
            return False
        else:
            return True
