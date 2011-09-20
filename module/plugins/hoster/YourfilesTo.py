#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class YourfilesTo(Hoster):
    __name__ = "YourfilesTo"
    __type__ = "hoster"
    __pattern__ = r"(http://)?(www\.)?yourfiles\.(to|biz)/\?d=[a-zA-Z0-9]+"
    __version__ = "0.2"
    __description__ = """Youfiles.to Download Hoster"""
    __author_name__ = ("jeix", "skydancer")
    __author_mail__ = ("jeix@hasnomail.de", "skydancer@hasnomail.de")

    def setup(self):
        self.html = None
        self.multiDL = True

    def process(self,pyfile):
        self.pyfile = pyfile
        self.prepare()
        self.download(self.get_file_url())
    
    def prepare(self):
        if not self.file_exists():
            self.offline()

        self.pyfile.name = self.get_file_name()
        
        wait_time = self.get_waiting_time()
        self.setWait(wait_time)
        self.log.debug("%s: Waiting %d seconds." % (self.__name__,wait_time))
        self.wait()

    def get_waiting_time(self):
        if self.html is None:
            self.download_html()
            
        #var zzipitime = 15;
        m = re.search(r'var zzipitime = (\d+);', self.html)
        if m:
            sec = int(m.group(1))
        else:
            sec = 0
            
        return sec
        
    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        url = re.search(r"var bla = '(.*?)';", self.html)
        if url:
            url = url.group(1)
            url = urllib.unquote(url.replace("http://http:/http://", "http://").replace("dumdidum", ""))
            return url
        else:
            self.fail("absolute filepath could not be found. offline? ")
       
    def get_file_name(self):
        if self.html is None:
            self.download_html()

        return re.search("<title>(.*)</title>", self.html).group(1)

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
            
        if re.search(r"HTTP Status 404", self.html) is not None:
            return False
        else:
            return True

        

