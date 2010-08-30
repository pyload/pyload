#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class PornhostCom(Hoster):
    __name__ = "PornhostCom"
    __type__ = "hoster"
    __pattern__ = r'http://[\w\.]*?pornhost\.com/([0-9]+/[0-9]+\.html|[0-9]+)'
    __version__ = "0.2"
    __description__ = """Pornhost.com Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()
            
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())
        

    ###   old interface
    def download_html(self):
        url = self.pyfile.url
        self.html = self.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html is None:
            self.download_html()

        file_url = re.search(r'download this file</label>.*?<a href="(.*?)"', self.html)
        if not file_url: 
            file_url = re.search(r'"(http://dl[0-9]+\.pornhost\.com/files/.*?/.*?/.*?/.*?/.*?/.*?\..*?)"', self.html)
            if not file_url:
                file_url = re.search(r'width: 894px; height: 675px">.*?<img src="(.*?)"', self.html)
                if not file_url:
                    file_url = re.search(r'"http://file[0-9]+\.pornhost\.com/[0-9]+/.*?"', self.html) # TODO: fix this one since it doesn't match

        file_url = file_url.group(1).strip()
                    
        return file_url
    
    def get_file_name(self):
        if self.html is None:
            self.download_html()
            
        name = re.search(r'<title>pornhost\.com - free file hosting with a twist - gallery(.*?)</title>', self.html)
        if not name:
            name = re.search(r'id="url" value="http://www\.pornhost\.com/(.*?)/"', self.html)
            if not name:
                name = re.search(r'<title>pornhost\.com - free file hosting with a twist -(.*?)</title>', self.html)
                if not name:
                    name = re.search(r'"http://file[0-9]+\.pornhost\.com/.*?/(.*?)"', self.html)
       
        name = name.group(1).strip() + ".flv"
        
        return name

    def file_exists(self):
        """ returns True or False
        """
        if self.html is None:
            self.download_html()
        
        if re.search(r'gallery not found', self.html) is not None \
        or re.search(r'You will be redirected to', self.html) is not None:
            return False
        else:
            return True
            
            
