#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.Hoster import Hoster
from module.unescape import unescape

class RedtubeCom(Hoster):
    __name__ = "RedtubeCom"
    __type__ = "hoster"
    __pattern__ = r'http://[\w\.]*?redtube\.com/\d+'
    __version__ = "0.1"
    __description__ = """Redtube.com Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        
    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()

        file_url = unescape(re.search(r'hashlink=(http.*?)"', self.html).group(1))

        return file_url
    
    def get_file_name(self):
        if self.html == None:
            self.download_html()
            
        name = re.search('<title>(.*?)- RedTube - Free Porn Videos</title>', self.html).group(1).strip() + ".flv"        
        return name

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        
        if re.search(r'This video has been removed.', self.html) != None:
            return False
        else:
            return True
            
