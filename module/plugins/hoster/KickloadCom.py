#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

class KickloadCom(Hoster):
    __name__ = "KickloadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www)?\.?(?:storage\.to|kickload\.com)/get/.*"
    __version__ = "0.2"
    __description__ = """Storage.to / Kickload.com Download Hoster"""
    __author_name__ = ("mkaay")

    def setup(self):
        self.wantReconnect = False
        self.api_data = None
        self.html = None
        self.multiDL = False
        
    def process(self, pyfile):
        self.pyfile = pyfile
        self.prepare()
        self.download( self.get_file_url() )
        
    def prepare(self):
        pyfile = self.pyfile
        
        self.wantReconnect = False

        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        
        self.setWait( self.get_wait_time() )

        while self.wantReconnect:
            self.wait()
            self.download_api_data()
            self.setWait(  self.get_wait_time() )
        
        return True
    
    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def download_api_data(self):
        url = self.pyfile.url
        info_url = url.replace("/get/", "/getlink/")
        src = self.load(info_url)
        if "To download this file you need a premium account" in src:
            self.fail("Need premium account for this file")
        
        pattern = re.compile(r"'(\w+)' : (.*?)[,|\}]")
        self.api_data = {}
        for pair in pattern.findall(src):
            self.api_data[pair[0]] = pair[1].strip("'")
        print self.api_data

    def get_wait_time(self):
        if not self.api_data:
            self.download_api_data()
        if self.api_data["state"] == "wait":
            self.wantReconnect = True
        else:
            self.wantReconnect = False
            
        return int(self.api_data["countdown"]) + 3
            
            

    def file_exists(self):
        """ returns True or False
        """
        if not self.api_data:
            self.download_api_data()
        if self.api_data["state"] == "failed":
            return False
        else:
            return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.api_data:
            self.download_api_data()
        return self.api_data["link"]

    def get_file_name(self):
        if not self.html:
            self.download_html()
        file_name_pattern = r"<span class=\"orange\">Downloading:</span>(.*?)<span class=\"light\">(.*?)</span>"
        return re.search(file_name_pattern, self.html).group(1).strip()
