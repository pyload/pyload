#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

class EasyShareCom(Hoster):
    __name__ = "EasyShareCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\d\.]*?easy-share\.com/(\d{6}).*"
    __version__ = "0.1"
    __description__ = """easy-share.com One-Klick Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")

    
    def setup(self):
        self.multiDL = False
        self.html = None

    def process(self, pyfile):
        self.pyfile = pyfile
        
        self.html = self.load(self.pyfile.url)
        self.pyfile.name = self.getFileName()
        
        self.download( self.getFileUrl() )
        
    
    def getFileName(self):
        return re.search(r'requesting:</span>\s*(.*?)<', self.html).group(1)

        
    def getFileUrl(self):
    
        if "There is another download in progress from your IP" in self.html:
            self.log.info("%s: IP blocked, retry in 5 minutes." % self.__name__)
            self.setWait(5 * 60)
            self.wait()
            self.retry()
            
        if "You need a premium membership to download this file" in self.html:
            self.fail("You need a premium membership to download this file.")
    
    
        wait = re.search(r"w='(\d+)'", self.html)
        if wait:
            wait = int( wait.group(1).strip() )
            self.log.info("%s: Waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait)
            self.wait()

        tempurl = self.pyfile.url
        if not tempurl.endswith("/"):
            tempurl += "/"
        id = re.search(r'http://[\w\d\.]*?easy-share\.com/(\d+)/', tempurl).group(1)
        self.html = self.load("http://www.easy-share.com/file_contents/captcha/" + id)
        
        challenge = re.search(r'Recaptcha\.create\("(.*?)"', self.html).group(1)
        re_captcha = ReCaptcha(self)
        challenge, result = re_captcha.challenge(challenge)
        
        link = re.search(r'<form\s+method="post"\s+action="(http://[\w\d\.]*?easy-share.com/file_contents/.*?)">', self.html).group(1)
        id = re.search(r'file/id/(\d+)/', link)
        self.download( link, post={"id" : id,
                               "recaptcha_challenge_field" : challenge,
                               "recaptcha_response_field": result} )
        
