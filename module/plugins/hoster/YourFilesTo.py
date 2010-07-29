#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster
from time import time

class YourfilesTo(Hoster):
    __name__ = "YourfilesTo"
    __type__ = "hoster"
    __pattern__ = r"(http://)?(www\.)?yourfiles\.to/\?d=[a-zA-Z0-9]+"
    __version__ = "0.1"
    __description__ = """Youfiles.to Download Hoster"""
    __author_name__ = ("jeix", "skydancer")
    __author_mail__ = ("jeix@hasnomail.de", "skydancer@hasnomail.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

        
    def prepare(self, thread):
        self.want_reconnect = False
        self.pyfile.status.exists = self.file_exists()

        if not self.pyfile.status.exists:
            return False

        self.pyfile.status.filename = self.get_file_name()
        
        self.get_waiting_time()
        self.pyfile.status.waituntil = self.time_plus_wait
        self.pyfile.status.url = self.get_file_url()
        self.pyfile.status.want_reconnect = self.want_reconnect
        thread.wait(self.parent)

        return True

    def get_waiting_time(self):
        if self.html == None:
            self.download_html()
            
        #var zzipitime = 15;
        m = re.search(r'var zzipitime = (\d+);', self.html)
        if m:
            sec = int(m.group(1))
        else:
            sec = 0
            
        self.time_plus_wait = time() + sec
        
    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        url = re.search(r"var bla = '(.*?)';", self.html).group(1)
        url = urllib.unquote(url.replace("http://http:/http://", "http://").replace("dumdidum", ""))
        return url;
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()

        return re.search("<title>(.*)</title>", self.html).group(1)

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
            
        if re.search(r"HTTP Status 404", self.html) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.req.download(url, location, cookies=True)
        

        