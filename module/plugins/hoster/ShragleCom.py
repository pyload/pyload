#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pycurl import FOLLOWLOCATION

from module.plugins.Hoster import Hoster
from module.plugins.internal.SimpleHoster import parseHtmlForm
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getURL

API_KEY = "078e5ca290d728fd874121030efb4a0d"

def parseFileInfo(self, url):
    file_id = re.match(self.__pattern__, url).group('ID')
    
    data = getURL(
        "http://www.cloudnator.com/api.php?key=%s&action=getStatus&fileID=%s" % (API_KEY, file_id),
        decode = True
        ).split()
    
    if len(data) == 4:
        name, size, md5, status = data
        size = int(size)
        
        if hasattr(self, "check_data"):
            self.checkdata = {"size": size, "md5": md5} 
            
        return name, size, 2 if status == "0" else 1, url
    else:
        return url, 0, 1, url

def getInfo(urls):
    for url in urls:
        file_info = parseFileInfo(plugin, url)
        yield file_info        

class ShragleCom(Hoster):
    __name__ = "ShragleCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www.)?(cloudnator|shragle).com/files/(?P<ID>.*?)/"
    __version__ = "0.20"
    __description__ = """Cloudnator.com (Shragle.com) Download PLugin"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    def setup(self):
        self.html = None
        self.multiDL = False
        self.check_data = None
        
    def process(self, pyfile):
        #get file status and info
        self.pyfile.name, self.pyfile.size, status = parseFileInfo(self, pyfile.url)[:3]
        if status != 2:     
            self.offline()
        
        self.handleFree()
        
    def handleFree(self):
        self.html = self.load(self.pyfile.url)
        
        #get wait time
        found = re.search('\s*var\sdownloadWait\s=\s(\d+);', self.html)
        self.setWait(int(found.group(1)) if found else 30)
        
        #parse download form
        action, inputs = parseHtmlForm('id="download', self.html)
        
        #solve captcha
        found = re.search('recaptcha/api/(?:challenge|noscript)?k=(.+?)', self.html)
        captcha_key = found.group(1) if found else "6LdEFb0SAAAAAAwM70vnYo2AkiVkCx-xmfniatHz"
               
        recaptcha = ReCaptcha(self)
        
        inputs['recaptcha_challenge_field'], inputs['recaptcha_response_field'] = recaptcha.challenge(captcha_key)
        self.wait()
        
        #validate
        self.req.http.c.setopt(FOLLOWLOCATION, 0)
        self.html = self.load(action, post = inputs)      
        
        found = re.search(r"Location\s*:\s*(\S*)", self.req.http.header, re.I)
        if found:
            self.correctCaptcha()
            download_url = found.group(1)
        else:
            if "Sicherheitscode falsch" in self.html:
                self.invalidCaptcha()
                self.retry(max_tries = 5, reason = "Invalid captcha")
            else:
                self.fail("Invalid session")
            
        #download
        self.req.http.c.setopt(FOLLOWLOCATION, 1)
        self.download(download_url)
        
        check = self.checkDownload({
            "ip_blocked": re.compile(r'<div class="error".*IP.*loading')
            })
        if check == "ip_blocked":
            self.setWait(1800, True)
            self.wait()
            self.retry()
            
            