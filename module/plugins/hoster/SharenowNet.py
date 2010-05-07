#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.unescape import unescape

class SharenowNet(Hoster):
    __name__ = "SharenowNet"
    __type__ = "hoster"
    __pattern__ = r'http://(www\.)?share-now\.net/files/\d+-.*?\.html'
    __version__ = "0.1"
    __description__ = """Share-Now.net Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.multi_dl = False

    def proceed(self, url, location):
        postData = {"Submit":"Download+Now",}
        dval = re.search(r'name="download" value="(.*?)"/>', self.html).group(1)
        if "Sicherheitscode eingeben" in self.html:
            # download captcha

            # get captcha code
            dval = "captchacode"
            
        postData["download"] = dval
        self.download(url, location, cookies=False, post=postData)

    def download_html(self):
        self.url = self.parent.url
        self.html = self.load(self.url)
     
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()            

        return re.search(r'method="post" action="(http://.*?\.share-now\.net/download\.php)">', self.html).group(1)

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        
        name = re.search(r'<span class="style1">Download -> (.*?)</span>', self.html, re.DOTALL).group(1)
        name = "%s" % unescape(name.encode("ascii", "ignore")).decode("utf-8").encode("ascii", "ignore").replace("+", " ")
        return name
      
    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
            
        if re.search(r'name="download" value="(.*?)"/>', self.html) == None:
            return False
        else:
            return True
            
