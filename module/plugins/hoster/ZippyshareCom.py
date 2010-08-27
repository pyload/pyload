#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class ZippyshareCom(Hoster):
    __name__ = "ZippyshareCom"
    __type__ = "hoster"
    __pattern__ = r"(http://)?www?\d{0,2}\.zippyshare.com/v/"
    __version__ = "0.2"
    __description__ = """Zippyshare.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def setup(self):
        self.html = None
        self.wantReconnect = False
        self.multiDL = False
    
    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        if not self.file_exists():
            self.offline()
            
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        file_url_pattern = r"var \w* = '(http%.*?)';"
        file_url_search = re.search(file_url_pattern, self.html).group(1)
        file_url = urllib.unquote(file_url_search.replace("nnn", "aaa").replace("unlg", "v").replace("serwus", "zippyshare"))
        return file_url
        
    def get_file_name(self):
        if self.html is None:
            self.download_html()
        if not self.wantReconnect:
            file_name = re.search(r'Name: </font> <font.*>(.*?)</font>', self.html).group(1)
            return file_name
        else:
            return self.pyfile.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        if re.search(r'File does not exist on this server', self.html) is not None:
            return False
        else:
            return True
