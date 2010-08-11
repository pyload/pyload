#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Hoster import Hoster

from module.network.Request import getURL

def getInfo(urls):
    url = "http://megaupload.com/mgr_linkcheck.php"
    
    ids = [x.split("=")[-1] for x in urls]
    
    i = 0
    post = {}
    for id in ids:
        post["id%i"%i] = id
        i += 1
        
    api = getURL(url, {}, post)
    api = [x.split("&") for x in re.split(r"&?(?=id[\d]+=)", api)]
    
    result = []
    i=0
    for data in api:
        if data[0].startswith("id"):
            tmp = [x.split("=") for x in data]
            if tmp[2][1] == "3":
                status = 3
            elif tmp[0][1] == "0":
                status = 2
            elif tmp[0][1] == "1":
                status = 1
            else:
                status = 3
            
            name = tmp[3][1]
            size = tmp[1][1]
            
            result.append( (name, size, status, urls[i] ) )
            i += 1
    
    yield result

class MegauploadCom(Hoster):
    __name__ = "MegauploadCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?(megaupload)\.com/.*?(\?|&)d=[0-9A-Za-z]+"
    __version__ = "0.1"
    __description__ = """Megaupload.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def setup(self):
        self.html = [None, None]
        self.multiDL = False
        
    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        if not self.file_exists():
            self.offline()
            
        self.setWait(45)
        self.wait()
            
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):        
        for i in range(5):
            self.html[0] = self.load(self.pyfile.url)
            try:
                url_captcha_html = re.search('(http://www.{,3}\.megaupload\.com/gencap.php\?.*\.gif)', self.html[0]).group(1)
            except:
                continue

            captcha = self.decryptCaptcha(url_captcha_html)
            captchacode = re.search('name="captchacode" value="(.*)"', self.html[0]).group(1)
            megavar = re.search('name="megavar" value="(.*)">', self.html[0]).group(1)
            self.html[1] = self.load(self.pyfile.url, post={"captcha": captcha, "captchacode": captchacode, "megavar": megavar})
            if re.search(r"Waiting time before each download begins", self.html[1]) != None:
                break

    def get_file_url(self):
        file_url_pattern = 'id="downloadlink"><a href="(.*)" onclick="'
        search = re.search(file_url_pattern, self.html[1])
        return search.group(1).replace(" ", "%20")

    def get_file_name(self):
        file_name_pattern = 'id="downloadlink"><a href="(.*)" onclick="'
        return re.search(file_name_pattern, self.html[1]).group(1).split("/")[-1]

    def file_exists(self):
        self.download_html()
        if re.search(r"Unfortunately, the link you have clicked is not available.", self.html[0]) != None or \
            re.search(r"Download limit exceeded", self.html[0]):
            return False
        return True
