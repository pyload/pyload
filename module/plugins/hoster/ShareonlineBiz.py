#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from base64 import b64decode
import hashlib
import random
from time import sleep

from module.plugins.Hoster import Hoster
from module.network.Request import getURL
from module.plugins.Plugin import chunks

    
def getInfo(urls):
    api_url_base = "http://www.share-online.biz/linkcheck/linkcheck.php"
    
    for chunk in chunks(urls, 90):
        api_param_file = {"links": "\n".join(x.replace("http://www.share-online.biz/dl/","") for x in chunk)} #api only supports old style links
        src = getURL(api_url_base, post=api_param_file)
        result = []
        for i, res in enumerate(src.split("\n")):
            if not res:
                continue
            fields = res.split(";")
            
            if fields[1] == "OK":
                status = 2
            elif fields[1] in ("DELETED", "NOT FOUND"):
                status = 1
            else:
                status = 3
                
            result.append((fields[2], int(fields[3]), status, chunk[i]))
        yield result

class ShareonlineBiz(Hoster):
    __name__ = "ShareonlineBiz"
    __type__ = "hoster"
    __pattern__ = r"(?:http://)?(?:www.)?share-online.biz/(download.php\?id=|dl/)"
    __version__ = "0.2"
    __description__ = """Shareonline.biz Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    def setup(self):
        #self.req.canContinue = self.multiDL = True if self.account else False
        # range request not working?
        self.multiDL = True if self.account else False

    def process(self, pyfile):
        self.convertURL()
        self.downloadAPIData()
        pyfile.name = self.api_data["filename"]
        pyfile.sync()
        
        self.downloadHTML()
        
        self.download(self.getFileUrl(), cookies=True)

    def downloadAPIData(self):
        api_url_base = "http://www.share-online.biz/linkcheck/linkcheck.php?md5=1"
        api_param_file = {"links": self.pyfile.url.replace("http://www.share-online.biz/dl/","")} #api only supports old style links
        src = self.load(api_url_base, cookies=False, post=api_param_file)
        
        fields = src.split(";")
        self.api_data = {}
        self.api_data["fileid"] = fields[0]
        self.api_data["status"] = fields[1]
        if not self.api_data["status"] == "OK":
            self.offline()
        self.api_data["filename"] = fields[2]
        self.api_data["size"] = fields[3] # in bytes
        self.api_data["checksum"] = fields[4].strip().lower().replace("\n\n", "") # md5

    def downloadHTML(self):
        self.html = self.load(self.pyfile.url, cookies=True)
        if not self.account:
            html = self.load("%s/free/" % self.pyfile.url, post={"dl_free":"1"}, cookies=True)
            if re.search(r"/failure/full/1", self.req.lastEffectiveURL):
                self.setWait(120)
                self.log.info("%s: no free slots, waiting 120 seconds" % (self.__name__))
                self.wait()
                self.retry()
            captcha = self.decryptCaptcha("http://www.share-online.biz/captcha.php", get={"rand":"0.%s" % random.randint(10**15,10**16)}, cookies=True)
                
            self.log.debug("%s Captcha: %s" % (self.__name__, captcha))
            sleep(3)
            
            html = self.load(self.pyfile.url, post={"captchacode": captcha}, cookies=True)
            if re.search(r"Der Download ist Ihnen zu langsam", html):
                #m = re.search("var timeout='(\d+)';", self.html[1])
                #self.waitUntil = time() + int(m.group(1)) if m else 30
                return True

            self.retry()
        else:
            if r"Die Nummer ist leider nicht richtig oder ausgelaufen!" in html:
                self.retry()
            return True
    
    def convertURL(self):
        if self.account:
            self.pyfile.url = self.pyfile.url.replace("http://www.share-online.biz/dl/", "http://www.share-online.biz/download.php?id=")
            self.pyfile.url = self.pyfile.url.replace("http://www.share-online.biz/dl/", "http://share-online.biz/download.php?id=")
        else:
            self.pyfile.url = self.pyfile.url.replace("http://www.share-online.biz/download.php?id=", "http://www.share-online.biz/dl/")
            self.pyfile.url = self.pyfile.url.replace("http://share-online.biz/download.php?id=", "http://www.share-online.biz/dl/")
    
    def getFileUrl(self):
        """ returns the absolute downloadable filepath
        """
        if self.account:
            return re.search('<b>The following link contains a ticket to a valid mirror for your desired file\.</b>.*?<a href="(.*?)" onmouseout', self.html, re.S).group(1)
        file_url_pattern = 'loadfilelink\.decode\("([^"]+)'
        return b64decode(re.search(file_url_pattern, self.html).group(1))

    def checksum(self, local_file):
        if self.api_data and self.api_data["checksum"]:
            h = hashlib.md5()
            f = open(local_file, "rb")
            h.update(f.read())
            f.close()
            hexd = h.hexdigest()
            if hexd == self.api_data["checksum"]:
                return (True, 0)
            else:
                return (False, 1)
        else:
            return (True, 5)
