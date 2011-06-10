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

    def setup(self):
        self.html = None
        self.multiDL = False
        
    def process(self, pyfile):
        self.pyfile = pyfile
        
        if not self.file_exists():
            self.offline()
            
        self.pyfile.name = self.get_file_name()
        
        self.setWait(self.get_waiting_time())
        self.wait()
        
        self.proceed(self.get_file_url())

    def get_waiting_time(self):
        if self.html is None:
            self.download_html()

        timestring = re.search('\s*var\sdownloadWait\s=\s(\d*);', self.html)
        if timestring: 
            return int(timestring.group(1))
        else:
            return 10

    def download_html(self):
        self.html = self.load(self.pyfile.url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        self.fileID = re.search(r'name="fileID"\svalue="(.*?)"', self.html).group(1)
        self.dlSession = re.search(r'name="dlSession"\svalue="(.*?)"', self.html).group(1)
        self.userID = re.search(r'name="userID"\svalue="(.*?)"', self.html).group(1)
        self.password = re.search(r'name="password"\svalue="(.*?)"', self.html).group(1)
        self.lang = re.search(r'name="lang"\svalue="(.*?)"', self.html).group(1)
        return re.search(r'id="download"\saction="(.*?)"', self.html).group(1)

    def get_file_name(self):
        if self.html is None:
            self.download_html()

        #file_name_pattern = r'You want to download  \xc2\xbb<strong>(.*?)</strong>\xc2\xab'
        file_name_pattern = r'<h2 class="colorgrey center" style="overflow:hidden;width:1000px;"> (.*)<br /><span style="font-size:12px;font-weight:normal; width:100px;"> ([\d\.]*) MB</span></h2>'
        res = re.search(file_name_pattern, self.html)
        if res:
            return res.group(1)
        else:
            self.fail("filename cant be extracted")

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()

        if re.search(r"html", self.html) is None:
            return False
        else:
            return True

    def proceed(self, url):
        self.download(url, post={'fileID': self.fileID, 'dlSession': self.dlSession, 'userID': self.userID, 'password': self.password, 'lang': self.lang})
